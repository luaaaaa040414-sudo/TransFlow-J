"""
期刊管理 API + 校对 API + 报告 API + 模型配置 API
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.database import (
    Journal, ModelConfig, ReviewIssue, Decision, Segment,
    QualityReport, Project, TerminologyEntry,
)
import os
import time
import logging
import httpx
from app.core.config import settings
from app.schemas.schemas import (
    JournalCreate, JournalResponse,
    ModelConfigCreate, ModelConfigResponse,
    IssueResponse, IssueDecision,
    QualityReportResponse,
    APIKeysSchema, TestProviderRequest,
)
from app.services.mqm_review import mqm_review_service
from app.services.quality_checker import quality_checker

logger = logging.getLogger(__name__)

# ============================================================
# 期刊 API
# ============================================================

journals_router = APIRouter(prefix="/journals", tags=["期刊管理"])


@journals_router.post("", response_model=JournalResponse, summary="添加期刊")
def create_journal(data: JournalCreate, db: Session = Depends(get_db)):
    journal = Journal(**data.model_dump())
    db.add(journal)
    db.commit()
    db.refresh(journal)
    return journal


@journals_router.get("", response_model=List[JournalResponse], summary="搜索/列出期刊")
def list_journals(
    search: Optional[str] = None,
    domain: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Journal).filter(Journal.is_active == True)
    if search:
        query = query.filter(
            Journal.name.ilike(f"%{search}%") |
            Journal.abbreviation.ilike(f"%{search}%")
        )
    if domain:
        query = query.filter(Journal.domain.ilike(f"%{domain}%"))
    return query.offset(skip).limit(limit).all()


@journals_router.get("/{journal_id}", response_model=JournalResponse, summary="获取期刊详情")
def get_journal(journal_id: int, db: Session = Depends(get_db)):
    journal = db.query(Journal).filter(Journal.id == journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="期刊不存在")
    return journal


@journals_router.put("/{journal_id}", summary="更新期刊信息")
def update_journal(journal_id: int, data: JournalCreate, db: Session = Depends(get_db)):
    journal = db.query(Journal).filter(Journal.id == journal_id).first()
    if not journal:
        raise HTTPException(status_code=404, detail="期刊不存在")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(journal, field, value)
    db.commit()
    db.refresh(journal)
    return journal


# ============================================================
# 模型配置 API
# ============================================================

models_router = APIRouter(prefix="/models", tags=["模型配置"])


@models_router.get("/settings/keys", response_model=APIKeysSchema, summary="获取在线配置的 API Keys")
def get_api_keys():
    return APIKeysSchema(
        openai_api_key=settings.openai_api_key or "",
        openai_base_url=settings.openai_base_url or "https://api.openai.com/v1",
        deepseek_api_key=settings.deepseek_api_key or "",
        deepseek_base_url=settings.deepseek_base_url or "https://api.deepseek.com/v1",
        anthropic_api_key=settings.anthropic_api_key or "",
        custom_api_key=settings.custom_api_key or "",
        custom_base_url=settings.custom_base_url or "",
    )


@models_router.post("/settings/keys", summary="在线保存并持久化 API Keys")
def save_api_keys(data: APIKeysSchema):
    updates = data.model_dump(exclude_none=True)
    env_updates = {
        "OPENAI_API_KEY": data.openai_api_key or "",
        "OPENAI_BASE_URL": data.openai_base_url or "https://api.openai.com/v1",
        "DEEPSEEK_API_KEY": data.deepseek_api_key or "",
        "DEEPSEEK_BASE_URL": data.deepseek_base_url or "https://api.deepseek.com/v1",
        "ANTHROPIC_API_KEY": data.anthropic_api_key or "",
        "CUSTOM_API_KEY": data.custom_api_key or "",
        "CUSTOM_BASE_URL": data.custom_base_url or "",
    }
    for field, val in updates.items():
        if hasattr(settings, field):
            setattr(settings, field, val or "")

    env_file = os.path.abspath(".env")
    existing_lines = []
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            existing_lines = f.readlines()

    new_lines = []
    written_keys = set()
    for line in existing_lines:
        line_matched = False
        for k, v in env_updates.items():
            if line.strip().startswith(f"{k}=") or line.strip().startswith(f"{k} ="):
                new_lines.append(f'{k}="{v}"\n')
                written_keys.add(k)
                line_matched = True
                break
        if not line_matched:
            new_lines.append(line)

    for k, v in env_updates.items():
        if k not in written_keys:
            new_lines.append(f'{k}="{v}"\n')

    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return {"success": True, "message": "API Keys 已在线保存并即时生效！"}


@models_router.post("/test-provider", summary="测试指定提供商连通性")
async def test_provider_connection(req: TestProviderRequest):
    provider = req.provider.lower().strip()
    api_key = req.api_key or ""
    base_url = req.base_url or ""
    model = req.model or ""

    if not api_key:
        if provider == "openai":
            api_key = settings.openai_api_key
        elif provider == "deepseek":
            api_key = settings.deepseek_api_key
        elif provider == "anthropic":
            api_key = settings.anthropic_api_key
        elif provider == "custom":
            api_key = settings.custom_api_key

    if not base_url:
        if provider == "openai":
            base_url = settings.openai_base_url or "https://api.openai.com/v1"
        elif provider == "deepseek":
            base_url = settings.deepseek_base_url or "https://api.deepseek.com/v1"
        elif provider == "custom":
            base_url = settings.custom_base_url

    if not model:
        if provider == "openai":
            model = "gpt-4o"
        elif provider == "deepseek":
            model = "deepseek-chat"
        elif provider == "anthropic":
            model = "claude-3-5-sonnet-20241022"
        elif provider == "custom":
            model = settings.custom_model_id or "gpt-3.5-turbo"

    if not api_key:
        return {
            "success": False,
            "provider": provider,
            "error": f"{provider.upper()} API Key 尚未填入，请先填写后再测试连接",
        }

    start_t = time.time()
    try:
        if provider == "anthropic":
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": model,
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Reply OK"}],
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
                resp.raise_for_status()
                text = resp.json()["content"][0]["text"].strip()
        else:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Reply OK"}],
                "max_tokens": 10,
            }
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(f"{base_url.rstrip('/')}/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"].strip()

        latency_ms = int((time.time() - start_t) * 1000)
        return {
            "success": True,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "response": text,
            "message": f"连接成功！响应延迟 {latency_ms} ms",
        }
    except Exception as e:
        latency_ms = int((time.time() - start_t) * 1000)
        logger.error(f"测试模型连接失败 {provider} / {model}: {e}")
        return {
            "success": False,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "error": str(e),
        }


@models_router.post("", response_model=ModelConfigResponse, summary="添加模型配置")
def create_model_config(data: ModelConfigCreate, db: Session = Depends(get_db)):
    config = ModelConfig(**data.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@models_router.get("", response_model=List[ModelConfigResponse], summary="获取所有模型配置")
def list_model_configs(
    use_for: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ModelConfig).filter(ModelConfig.is_active == True)
    if use_for == "translation":
        query = query.filter(ModelConfig.use_for_translation == True)
    elif use_for == "proofreading":
        query = query.filter(ModelConfig.use_for_proofreading == True)
    return query.all()


@models_router.delete("/{config_id}", summary="删除模型配置")
def delete_model_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(ModelConfig).filter(ModelConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(config)
    db.commit()
    return {"success": True}


# ============================================================
# 校对 API
# ============================================================

proofreading_router = APIRouter(prefix="/proofreading", tags=["校对"])


async def _get_journal_style(db: Session, project_id: int) -> Optional[dict]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not project.journal_id:
        return None
    journal = db.query(Journal).filter(Journal.id == project.journal_id).first()
    if not journal:
        return None
    return {
        "name": journal.name,
        "english_variant": journal.english_variant,
        "style_rules": journal.style_rules or {},
    }


@proofreading_router.post("/segment/{segment_db_id}", summary="对单个段落进行 MQM 校对")
async def proofread_segment(
    segment_db_id: int,
    provider: str = "openai",
    model: str = "gpt-4o",
    db: Session = Depends(get_db),
):
    seg = db.query(Segment).filter(Segment.id == segment_db_id).first()
    if not seg:
        raise HTTPException(status_code=404, detail="段落不存在")

    if not seg.translated_text:
        raise HTTPException(status_code=400, detail="该段落尚未翻译")

    # 获取术语表和期刊风格
    terms = db.query(TerminologyEntry).filter(
        TerminologyEntry.project_id == seg.project_id,
        TerminologyEntry.status == "confirmed",
    ).all()
    terminology_map = {t.source_term: t.confirmed_translation for t in terms if t.confirmed_translation}

    journal_style = await _get_journal_style(db, seg.project_id)

    result = await mqm_review_service.review_segment(
        source_text=seg.source_text,
        translated_text=seg.translated_text,
        segment_id=seg.segment_id,
        provider=provider,
        model=model,
        terminology_map=terminology_map,
        journal_style=journal_style,
    )

    if result["success"]:
        # 保存问题到数据库
        # 先删除该段落该模型的旧问题
        db.query(ReviewIssue).filter(
            ReviewIssue.segment_id_fk == seg.id,
            ReviewIssue.detection_model == model,
        ).delete(synchronize_session=False)

        saved_issues = []
        for issue_data in result["issues"]:
            issue = ReviewIssue(
                segment_id_fk=seg.id,
                project_id=seg.project_id,
                error_type=issue_data.get("error_type", "Accuracy"),
                error_subtype=issue_data.get("error_subtype"),
                severity=issue_data.get("severity", "minor"),
                source_span=issue_data.get("source_span"),
                translation_span=issue_data.get("translation_span"),
                explanation=issue_data.get("explanation", ""),
                suggested_revision=issue_data.get("suggested_revision"),
                evidence=issue_data.get("evidence"),
                detected_by=f"{provider}/{model}",
                detection_model=model,
                human_status="pending",
            )
            db.add(issue)
            saved_issues.append(issue)

        if len(saved_issues) == 0:
            seg.status = "approved"
        else:
            seg.status = "reviewing"
        db.commit()

        return {
            "success": True,
            "segment_id": seg.segment_id,
            "status": seg.status,
            "issue_count": len(saved_issues),
            "severity_counts": result["severity_counts"],
            "issues": result["issues"],
        }
    else:
        raise HTTPException(status_code=500, detail=f"校对失败: {result.get('error')}")


@proofreading_router.get("/issues/{project_id}", summary="获取项目所有校对问题")
def list_issues(
    project_id: int,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ReviewIssue).filter(ReviewIssue.project_id == project_id)
    if status:
        query = query.filter(ReviewIssue.human_status == status)
    if severity:
        query = query.filter(ReviewIssue.severity == severity)
    issues = query.order_by(ReviewIssue.created_at.desc()).all()

    return [
        {
            "id": i.id,
            "segment_id_fk": i.segment_id_fk,
            "error_type": i.error_type,
            "error_subtype": i.error_subtype,
            "severity": i.severity,
            "source_span": i.source_span,
            "translation_span": i.translation_span,
            "explanation": i.explanation,
            "suggested_revision": i.suggested_revision,
            "evidence": i.evidence,
            "detected_by": i.detected_by,
            "human_status": i.human_status,
            "human_decision_text": i.human_decision_text,
            "decided_at": i.decided_at,
            "created_at": i.created_at,
        }
        for i in issues
    ]


@proofreading_router.put("/issue/{issue_id}/decide", summary="人工裁决校对问题")
def decide_issue(
    issue_id: int,
    decision: IssueDecision,
    db: Session = Depends(get_db),
):
    issue = db.query(ReviewIssue).filter(ReviewIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")

    issue.human_status = decision.human_status
    issue.human_decision_text = decision.human_decision_text
    issue.decided_at = datetime.utcnow()

    # 如果是 modified 或 accepted 且提供了最终译文，更新段落
    if decision.human_status in ("modified", "accepted") and decision.final_text:
        seg = db.query(Segment).filter(Segment.id == issue.segment_id_fk).first()
        if seg:
            old_text = seg.translated_text
            seg.translated_text = decision.final_text
            seg.status = "approved"

            history = Decision(
                segment_id_fk=seg.id,
                project_id=seg.project_id,
                action="edit",
                before_text=old_text,
                after_text=decision.final_text,
                reason=f"采纳校对建议（问题 #{issue_id}）",
            )
            db.add(history)

    # 检查该段落是否还有待裁决的问题；若全部处理完毕且处于校对中，自动转为 approved
    remaining_pending = db.query(ReviewIssue).filter(
        ReviewIssue.segment_id_fk == issue.segment_id_fk,
        ReviewIssue.human_status == "pending",
        ReviewIssue.id != issue.id,
    ).count()
    if remaining_pending == 0:
        seg = db.query(Segment).filter(Segment.id == issue.segment_id_fk).first()
        if seg and seg.status == "reviewing":
            seg.status = "approved"

    db.commit()
    return {"success": True, "issue_id": issue_id, "status": decision.human_status}


# ============================================================
# 质量报告 API
# ============================================================

reports_router = APIRouter(prefix="/reports", tags=["质量报告"])


@reports_router.post("/generate/{project_id}", summary="生成项目质量报告")
def generate_report(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取所有段落
    segments = db.query(Segment).filter(Segment.project_id == project_id).all()
    seg_dicts = [
        {
            "segment_id": s.segment_id,
            "source_text": s.source_text,
            "translated_text": s.translated_text,
            "initial_translation": s.initial_translation,
            "status": s.status,
            "has_flag": s.has_flag,
        }
        for s in segments
    ]

    # 获取确认术语表
    terms = db.query(TerminologyEntry).filter(
        TerminologyEntry.project_id == project_id,
        TerminologyEntry.status == "confirmed",
    ).all()
    terminology_map = {t.source_term: t.confirmed_translation for t in terms if t.confirmed_translation}

    # 运行质量检查
    report_data = quality_checker.generate_project_report(seg_dicts, terminology_map)

    # 获取 MQM 问题统计
    all_issues = db.query(ReviewIssue).filter(ReviewIssue.project_id == project_id).all()
    total_issues = len(all_issues)
    critical_issues = sum(1 for i in all_issues if i.severity == "critical")
    major_issues = sum(1 for i in all_issues if i.severity == "major")
    minor_issues = sum(1 for i in all_issues if i.severity == "minor")
    resolved = sum(1 for i in all_issues if i.human_status in ("accepted", "rejected", "modified"))

    # 计算采纳率
    accepted = sum(1 for i in all_issues if i.human_status in ("accepted", "modified"))
    adoption_rate = accepted / resolved if resolved > 0 else None

    # 保存报告
    report = QualityReport(
        project_id=project_id,
        total_segments=report_data["total_segments"],
        translated_segments=report_data["translated_segments"],
        approved_segments=report_data["approved_segments"],
        flagged_segments=report_data["flagged_segments"],
        total_issues=total_issues,
        critical_issues=critical_issues,
        major_issues=major_issues,
        minor_issues=minor_issues,
        resolved_issues=resolved,
        number_errors=report_data["number_errors"],
        terminology_consistency_rate=report_data.get("terminology_consistency_rate"),
        adoption_rate=adoption_rate,
        human_edit_rate=report_data.get("human_edit_rate"),
        check_scope=f"共检查 {report_data['translated_segments']} 个已翻译段落",
        report_data=report_data,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.id,
        "project_id": project_id,
        "generated_at": report.generated_at.isoformat() if report.generated_at else datetime.utcnow().isoformat(),
        "summary": {
            "total_segments": report.total_segments,
            "translated_segments": report.translated_segments,
            "approved_segments": report.approved_segments,
            "flagged_segments": report.flagged_segments,
            "progress_percent": round(
                report.translated_segments / report.total_segments * 100, 1
            ) if report.total_segments > 0 else 0,
        },
        "quality": {
            "number_errors": report.number_errors,
            "number_errors_pass": report.number_errors == 0,
            "terminology_consistency_rate": report.terminology_consistency_rate,
            "terminology_pass": (
                report.terminology_consistency_rate is None or
                report.terminology_consistency_rate >= 0.98
            ),
            "adoption_rate": report.adoption_rate,
            "human_edit_rate": report.human_edit_rate,
        },
        "issues": {
            "total": total_issues,
            "critical": critical_issues,
            "major": major_issues,
            "minor": minor_issues,
            "resolved": resolved,
            "pending": total_issues - resolved,
        },
        "detail": report_data,
    }


@reports_router.get("/{project_id}", summary="获取项目历史报告列表")
def list_reports(project_id: int, db: Session = Depends(get_db)):
    reports = db.query(QualityReport).filter(
        QualityReport.project_id == project_id
    ).order_by(QualityReport.generated_at.desc()).all()
    return reports


@reports_router.get("/detail/{report_id}", summary="获取报告详情")
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(QualityReport).filter(QualityReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return report
