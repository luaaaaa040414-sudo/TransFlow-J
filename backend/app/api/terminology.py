"""
术语管理 API
术语创建、查证记录、信源证据、确认状态管理
"""
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.database import TerminologyEntry, SourceEvidence
from app.schemas.schemas import (
    TermCreate, TermUpdate, TermResponse,
    EvidenceCreate, EvidenceResponse,
)
from app.services.source_research import source_research_service

router = APIRouter(prefix="/terminology", tags=["术语管理"])


@router.post("/project/{project_id}", response_model=TermResponse, summary="创建术语条目")
def create_term(project_id: int, data: TermCreate, db: Session = Depends(get_db)):
    # 检查是否已存在
    existing = db.query(TerminologyEntry).filter(
        TerminologyEntry.project_id == project_id,
        TerminologyEntry.source_term == data.source_term,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"术语「{data.source_term}」已存在")

    term = TerminologyEntry(project_id=project_id, **data.model_dump())
    db.add(term)
    db.commit()
    db.refresh(term)
    return _term_to_response(term, db)


@router.get("/project/{project_id}", summary="获取项目所有术语")
def list_terms(
    project_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(TerminologyEntry).filter(TerminologyEntry.project_id == project_id)
    if status:
        query = query.filter(TerminologyEntry.status == status)
    terms = query.order_by(TerminologyEntry.created_at.desc()).all()
    return [_term_to_response(t, db) for t in terms]


@router.get("/{term_id}", summary="获取术语详情（含证据）")
def get_term(term_id: int, db: Session = Depends(get_db)):
    term = db.query(TerminologyEntry).filter(TerminologyEntry.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="术语不存在")
    return _term_to_response(term, db)


@router.put("/{term_id}", summary="更新术语状态/确认译法")
def update_term(term_id: int, data: TermUpdate, db: Session = Depends(get_db)):
    term = db.query(TerminologyEntry).filter(TerminologyEntry.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="术语不存在")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(term, field, value)
    db.commit()
    db.refresh(term)
    return _term_to_response(term, db)


@router.delete("/{term_id}", summary="删除术语")
def delete_term(term_id: int, db: Session = Depends(get_db)):
    term = db.query(TerminologyEntry).filter(TerminologyEntry.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="术语不存在")
    db.delete(term)
    db.commit()
    return {"success": True}


@router.post("/{term_id}/auto-research", summary="依据信源优先级自动检索权威证据")
async def auto_research_term(term_id: int, db: Session = Depends(get_db)):
    term = db.query(TerminologyEntry).filter(TerminologyEntry.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="术语不存在")

    research_result = await source_research_service.execute_progressive_research(
        source_term=term.source_term,
        domain=term.domain
    )

    evidences = research_result.get("evidences", [])
    cards = research_result.get("cards", [])
    decomposition = research_result.get("decomposition", [])
    is_exact = research_result.get("is_exact", False)

    # 清除旧的无候选译法的占位记录，便于用最新检索证据替换
    db.query(SourceEvidence).filter(
        SourceEvidence.term_id == term.id,
        (SourceEvidence.candidate_translation == None) | (SourceEvidence.candidate_translation == "")
    ).delete()

    candidates = list(term.candidate_translations or [])
    for c in research_result.get("candidates", []):
        if c and c not in candidates:
            candidates.append(c)

    # 查重集合
    existing_keys = {
        (e.source_name, e.candidate_translation)
        for e in db.query(SourceEvidence).filter(SourceEvidence.term_id == term.id).all()
    }

    added_count = 0
    for ev_data in evidences:
        cand = (ev_data.get("candidate_translation") or "").strip()
        key = (ev_data.get("source_name"), cand or None)
        if key in existing_keys:
            continue

        evidence = SourceEvidence(
            term_id=term.id,
            source_level=ev_data["source_level"],
            source_type=ev_data.get("source_type"),
            source_name=ev_data.get("source_name"),
            source_url=ev_data.get("source_url"),
            evidence_text=ev_data.get("evidence_text"),
            candidate_translation=cand or None,
            published_date=ev_data.get("published_date"),
            is_valid=ev_data.get("is_valid", True),
        )
        db.add(evidence)
        existing_keys.add(key)
        added_count += 1

    term.candidate_translations = candidates

    # 状态与确认规则：
    # 如果是精确官方收录（is_exact=True）：直接自动确认为1级官方译法
    # 如果是组合拆解推导（is_exact=False）：提供推荐译法并生成清晰证据卡，但严守学术规范：
    # “核心术语已有证据，完整组合译法仍需确认，不会把部分证据冒充整个词的官方译法”
    if is_exact:
        if candidates and not term.confirmed_translation:
            term.confirmed_translation = candidates[0]
            term.status = "confirmed"

    # 将结构化卡片与拆解过程存入 notes 字段（JSON 格式），使前端随时可重现完整的证据卡
    notes_payload = {
        "is_exact": is_exact,
        "match_type": research_result.get("match_type"),
        "core_term": research_result.get("core_term"),
        "decomposition": decomposition,
        "recommendation_reason": research_result.get("recommendation_reason"),
        "cards": cards,
        "workflow_steps": [
            {"step": 1, "name": "完整词语检索", "desc": "搜索完整词条", "status": "hit" if is_exact else "missed"},
            {"step": 2, "name": "语义拆解分析", "desc": "识别核心专业术语与范围限定", "status": "skipped" if is_exact else "done"},
            {"step": 3, "name": "扩大权威信源", "desc": "1级官方 ➔ 2/3级行业标准与学术期刊", "status": "done"},
            {"step": 4, "name": "证据卡生成", "desc": "整理推荐译法、适用领域、原文、链接、推荐理由", "status": "done"}
        ]
    }
    term.notes = json.dumps(notes_payload, ensure_ascii=False)

    db.commit()
    db.refresh(term)
    return {
        "success": True,
        "added_evidence_count": added_count,
        "term": _term_to_response(term, db)
    }



# ============================================================
# 信源证据 API
# ============================================================

@router.post("/{term_id}/evidence", response_model=EvidenceResponse, summary="添加信源证据")
def add_evidence(term_id: int, data: EvidenceCreate, db: Session = Depends(get_db)):
    term = db.query(TerminologyEntry).filter(TerminologyEntry.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="术语不存在")

    evidence = SourceEvidence(term_id=term_id, **data.model_dump())
    db.add(evidence)

    # 自动更新术语的候选译法列表
    candidates = term.candidate_translations or []
    if data.candidate_translation and data.candidate_translation not in candidates:
        candidates.append(data.candidate_translation)
        term.candidate_translations = candidates

    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("/{term_id}/evidence", response_model=List[EvidenceResponse], summary="获取术语所有证据")
def list_evidence(term_id: int, db: Session = Depends(get_db)):
    return db.query(SourceEvidence).filter(
        SourceEvidence.term_id == term_id
    ).order_by(SourceEvidence.source_level).all()


@router.put("/evidence/{evidence_id}/verify", summary="确认/标记证据有效性")
def verify_evidence(
    evidence_id: int,
    is_valid: bool = True,
    verifier: str = "user",
    db: Session = Depends(get_db),
):
    ev = db.query(SourceEvidence).filter(SourceEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="证据不存在")
    ev.is_valid = is_valid
    ev.verified_by = verifier
    ev.verified_at = datetime.utcnow()
    db.commit()
    return {"success": True, "is_valid": is_valid}


@router.post("/{term_id}/confirm", summary="确认术语最终译法")
def confirm_term(
    term_id: int,
    confirmed_translation: str,
    db: Session = Depends(get_db),
):
    term = db.query(TerminologyEntry).filter(TerminologyEntry.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="术语不存在")
    term.confirmed_translation = confirmed_translation
    term.status = "confirmed"
    db.commit()
    return {"success": True, "confirmed_translation": confirmed_translation}


# ============================================================
# 辅助函数
# ============================================================

def _term_to_response(term: TerminologyEntry, db: Session) -> dict:
    evidences = db.query(SourceEvidence).filter(
        SourceEvidence.term_id == term.id
    ).order_by(SourceEvidence.source_level).all()

    cards = []
    decomposition = None
    parsed_meta = {}
    if term.notes:
        try:
            parsed_meta = json.loads(term.notes)
            if isinstance(parsed_meta, dict):
                cards = parsed_meta.get("cards", [])
                decomposition = parsed_meta.get("decomposition")
        except Exception:
            parsed_meta = {"raw_notes": term.notes}

    # 如果历史数据没有 notes 证据卡，按 evidence 列表自动补齐卡片
    if not cards and evidences:
        for ev in evidences:
            cards.append({
                "recommended_translation": ev.candidate_translation or term.confirmed_translation or "",
                "domain": term.domain or "通用学术",
                "evidence_text": ev.evidence_text or "",
                "source_url": ev.source_url or "",
                "source_name": ev.source_name or ev.source_type or "权威信源",
                "source_level": ev.source_level,
                "recommendation_reason": "【国家权威机构名词库·直接收录】经国家科技名词审定委员会或官方校史沿革档案收录。" if ev.source_level == 1 else "【学术文献证据】经行业标准或国际同行评议顶级文献证实。",
                "match_type": "exact",
                "status_tag": "官方收录" if ev.source_level == 1 else "文献共识",
                "decomposition": None
            })

    return {
        "id": term.id,
        "source_term": term.source_term,
        "domain": term.domain,
        "candidate_translations": term.candidate_translations or [],
        "confirmed_translation": term.confirmed_translation,
        "status": term.status.value if hasattr(term.status, "value") else str(term.status),
        "notes": term.notes,
        "created_at": term.created_at,
        "cards": cards,
        "decomposition": decomposition,
        "research_summary": parsed_meta,
        "evidence": [
            {
                "id": e.id,
                "source_level": e.source_level,
                "source_type": e.source_type,
                "source_name": e.source_name,
                "source_url": e.source_url,
                "evidence_text": e.evidence_text,
                "candidate_translation": e.candidate_translation,
                "published_date": e.published_date,
                "is_valid": e.is_valid,
                "verified_at": e.verified_at,
                "created_at": e.created_at,
            }
            for e in evidences
        ],
    }
