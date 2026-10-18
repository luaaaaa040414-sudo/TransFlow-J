"""
翻译 API - 段落查看、翻译任务、人工编辑
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.database import Segment, Project, Decision, Journal, TerminologyEntry
from app.schemas.schemas import SegmentResponse, SegmentUpdate, TranslationRequest
from app.services.translation_service import translation_service
from app.services.quality_checker import quality_checker

router = APIRouter(prefix="/translation", tags=["翻译"])


def get_journal_style(db: Session, journal_id: Optional[int]) -> Optional[dict]:
    """获取期刊风格配置"""
    if not journal_id:
        return None
    journal = db.query(Journal).filter(Journal.id == journal_id).first()
    if not journal:
        return None
    return {
        "name": journal.name,
        "english_variant": journal.english_variant,
        "style_rules": journal.style_rules or {},
        "article_types": journal.article_types or [],
    }


def get_terminology_map(db: Session, project_id: int) -> dict:
    """获取项目已确认术语表"""
    terms = db.query(TerminologyEntry).filter(
        TerminologyEntry.project_id == project_id,
        TerminologyEntry.status == "confirmed",
        TerminologyEntry.confirmed_translation != None,
    ).all()
    return {t.source_term: t.confirmed_translation for t in terms}


@router.get("/segments/{project_id}", response_model=List[SegmentResponse], summary="获取项目所有段落")
def list_segments(
    project_id: int,
    status: Optional[str] = None,
    section: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(Segment).filter(Segment.project_id == project_id)
    if status:
        query = query.filter(Segment.status == status)
    if section:
        query = query.filter(Segment.section == section)
    return query.order_by(Segment.order_index).offset(skip).limit(limit).all()


@router.get("/segment/{segment_id_db}", response_model=SegmentResponse, summary="获取单个段落")
def get_segment(segment_id_db: int, db: Session = Depends(get_db)):
    seg = db.query(Segment).filter(Segment.id == segment_id_db).first()
    if not seg:
        raise HTTPException(status_code=404, detail="段落不存在")
    return seg


@router.put("/segment/{segment_id_db}", response_model=SegmentResponse, summary="人工编辑段落译文")
def update_segment(
    segment_id_db: int,
    data: SegmentUpdate,
    db: Session = Depends(get_db),
):
    seg = db.query(Segment).filter(Segment.id == segment_id_db).first()
    if not seg:
        raise HTTPException(status_code=404, detail="段落不存在")

    # 记录修改历史
    old_text = seg.translated_text
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(seg, field, value)

    # 如果修改了译文，记录到 decisions
    if data.translated_text and data.translated_text != old_text:
        decision = Decision(
            segment_id_fk=seg.id,
            project_id=seg.project_id,
            action="edit",
            before_text=old_text,
            after_text=data.translated_text,
        )
        db.add(decision)

        # 数字一致性检查
        num_result = quality_checker.check_segment(
            seg.source_text,
            data.translated_text,
            seg.segment_id,
        )
        seg.numbers_issues = num_result.get("number_issues", [])
        seg.numbers_verified = len(num_result.get("number_issues", [])) == 0

    db.commit()
    db.refresh(seg)
    return seg


@router.post("/translate/segment/{segment_id_db}", summary="翻译单个段落")
async def translate_segment(
    segment_id_db: int,
    provider: str = "openai",
    model: str = "gpt-4o",
    db: Session = Depends(get_db),
):
    seg = db.query(Segment).filter(Segment.id == segment_id_db).first()
    if not seg:
        raise HTTPException(status_code=404, detail="段落不存在")

    project = db.query(Project).filter(Project.id == seg.project_id).first()
    journal_id = project.journal_id if project else None
    journal_style = get_journal_style(db, journal_id)
    terminology_map = get_terminology_map(db, seg.project_id)
    article_type = project.article_type or "研究论文" if project else "研究论文"

    result = await translation_service.translate_segment(
        source_text=seg.source_text,
        segment_id=seg.segment_id,
        section=seg.section or "正文",
        provider_name=provider,
        model=model,
        journal_style=journal_style,
        terminology_map=terminology_map,
        article_type=article_type,
    )

    if result["success"]:
        # 保存初始译文（如果还没有）
        if not seg.initial_translation:
            seg.initial_translation = result["translated_text"]

        seg.translated_text = result["translated_text"]
        seg.status = "translated"
        seg.has_flag = result["has_flag"]
        if result["has_flag"]:
            reasons = [f["reason"] for f in result["flags"]]
            seg.flag_reason = "; ".join(reasons)
        seg.translation_model = model
        seg.translation_provider = provider
        seg.translated_at = datetime.utcnow()

        # 自动数字检查
        num_result = quality_checker.check_segment(
            seg.source_text,
            seg.translated_text,
            seg.segment_id,
        )
        seg.numbers_issues = num_result.get("number_issues", [])
        seg.numbers_verified = len(num_result.get("number_issues", [])) == 0

        db.commit()
        db.refresh(seg)

        return {
            "success": True,
            "segment": {
                "id": seg.id,
                "segment_id": seg.segment_id,
                "translated_text": seg.translated_text,
                "has_flag": seg.has_flag,
                "flags": result["flags"],
                "numbers_verified": seg.numbers_verified,
                "numbers_issues": seg.numbers_issues,
            },
        }
    else:
        raise HTTPException(status_code=500, detail=f"翻译失败: {result.get('error')}")


async def translate_project_task(
    project_id: int,
    segment_ids: Optional[List[int]],
    provider: str,
    model: str,
    db: Session,
):
    """后台任务：批量翻译项目段落"""
    query = db.query(Segment).filter(Segment.project_id == project_id)
    if segment_ids:
        query = query.filter(Segment.id.in_(segment_ids))
    else:
        query = query.filter(Segment.status == "pending")

    segments = query.order_by(Segment.order_index).all()

    project = db.query(Project).filter(Project.id == project_id).first()
    journal_style = get_journal_style(db, project.journal_id if project else None)
    terminology_map = get_terminology_map(db, project_id)
    article_type = project.article_type or "研究论文" if project else "研究论文"

    if project:
        project.status = "translating"
        db.commit()

    success_count = 0
    for seg in segments:
        result = await translation_service.translate_segment(
            source_text=seg.source_text,
            segment_id=seg.segment_id,
            section=seg.section or "正文",
            provider_name=provider,
            model=model,
            journal_style=journal_style,
            terminology_map=terminology_map,
            article_type=article_type,
        )
        if result["success"]:
            if not seg.initial_translation:
                seg.initial_translation = result["translated_text"]
            seg.translated_text = result["translated_text"]
            seg.status = "translated"
            seg.has_flag = result["has_flag"]
            seg.translation_model = model
            seg.translation_provider = provider
            seg.translated_at = datetime.utcnow()
            success_count += 1

    # 更新项目进度
    if project:
        translated = db.query(Segment).filter(
            Segment.project_id == project_id,
            Segment.translated_text != None,
        ).count()
        project.translated_segments = translated
        if translated >= project.total_segments:
            project.status = "translated"
        db.commit()


@router.post("/translate/project/{project_id}", summary="批量翻译项目段落（后台任务）")
async def translate_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    request: TranslationRequest = TranslationRequest(),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    provider = request.provider or project.translation_provider or settings.default_translation_provider
    model = request.model or project.translation_model or settings.default_translation_model

    background_tasks.add_task(
        translate_project_task,
        project_id,
        request.segment_ids,
        provider,
        model,
        db,
    )

    return {
        "success": True,
        "message": f"翻译任务已启动（提供商：{provider}，模型：{model}）",
        "project_id": project_id,
    }


@router.post("/test-connection", summary="测试 API 连通性")
async def test_connection(provider: str = "openai", model: str = "gpt-4o"):
    result = await translation_service.test_connection(provider, model)
    return result
