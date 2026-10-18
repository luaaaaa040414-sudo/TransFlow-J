"""
导出下载 API (Export & Download Routes)
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import urllib.parse

from app.core.database import get_db
from app.models.database import Project, Segment, TerminologyEntry, SourceEvidence, ReviewIssue, QualityReport
from app.services.export_service import export_service

router = APIRouter(prefix="/export", tags=["导出与归档"])


def _get_project_data(project_id: int, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    segments = db.query(Segment).filter(Segment.project_id == project_id).order_by(Segment.order_index).all()
    seg_list = [
        {
            "segment_id": s.segment_id,
            "section": s.section,
            "section_level": s.section_level,
            "source_text": s.source_text,
            "translated_text": s.translated_text,
            "initial_translation": s.initial_translation,
            "approved_text": s.approved_text,
            "status": s.status,
            "has_flag": s.has_flag,
            "flag_reason": s.flag_reason,
        }
        for s in segments
    ]

    terms = db.query(TerminologyEntry).filter(TerminologyEntry.project_id == project_id).all()
    term_list = []
    for t in terms:
        evs = db.query(SourceEvidence).filter(SourceEvidence.term_id == t.id).order_by(SourceEvidence.source_level).all()
        term_list.append({
            "source_term": t.source_term,
            "domain": t.domain,
            "confirmed_translation": t.confirmed_translation,
            "candidate_translations": t.candidate_translations or [],
            "status": t.status,
            "evidence": [
                {
                    "source_level": e.source_level,
                    "source_type": e.source_type,
                    "source_name": e.source_name,
                    "source_url": e.source_url,
                    "candidate_translation": e.candidate_translation,
                    "published_date": e.published_date,
                    "evidence_text": e.evidence_text,
                    "is_valid": e.is_valid
                }
                for e in evs
            ]
        })

    issues = db.query(ReviewIssue).filter(ReviewIssue.project_id == project_id).all()
    issue_list = []
    for i in issues:
        seg = db.query(Segment).filter(Segment.id == i.segment_id_fk).first()
        issue_list.append({
            "id": i.id,
            "segment_id": seg.segment_id if seg else "",
            "severity": i.severity,
            "error_type": i.error_type,
            "error_subtype": i.error_subtype,
            "detected_by": i.detected_by,
            "source_span": i.source_span,
            "translation_span": i.translation_span,
            "explanation": i.explanation,
            "suggested_revision": i.suggested_revision,
            "evidence": i.evidence,
            "human_status": i.human_status,
            "human_decision_text": i.human_decision_text
        })

    latest_report = db.query(QualityReport).filter(
        QualityReport.project_id == project_id
    ).order_by(QualityReport.generated_at.desc()).first()

    report_dict = None
    if latest_report:
        report_dict = {
            "id": latest_report.id,
            "total_segments": latest_report.total_segments,
            "translated_segments": latest_report.translated_segments,
            "number_errors": latest_report.number_errors,
            "terminology_consistency_rate": latest_report.terminology_consistency_rate,
            "adoption_rate": latest_report.adoption_rate,
            "human_edit_rate": latest_report.human_edit_rate,
        }

    return project, seg_list, term_list, issue_list, report_dict


@router.get("/english-docx/{project_id}", summary="导出英文论文稿 (.docx)")
def download_english_docx(project_id: int, db: Session = Depends(get_db)):
    project, seg_list, _, _, _ = _get_project_data(project_id, db)
    buf = export_service.export_english_docx(project.name, seg_list)
    filename = f"{project.name}_en.docx"
    encoded_name = urllib.parse.quote(filename)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_name}"}
    )


@router.get("/bilingual-docx/{project_id}", summary="导出中英逐段双语对照稿 (.docx)")
def download_bilingual_docx(project_id: int, db: Session = Depends(get_db)):
    project, seg_list, _, _, _ = _get_project_data(project_id, db)
    buf = export_service.export_bilingual_docx(project.name, seg_list)
    filename = f"{project.name}_bilingual.docx"
    encoded_name = urllib.parse.quote(filename)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_name}"}
    )


@router.get("/terminology-xlsx/{project_id}", summary="导出核定术语与信源证据表 (.xlsx)")
def download_terminology_xlsx(project_id: int, db: Session = Depends(get_db)):
    project, _, term_list, _, _ = _get_project_data(project_id, db)
    buf = export_service.export_terminology_excel(term_list)
    filename = f"{project.name}_terminology.xlsx"
    encoded_name = urllib.parse.quote(filename)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_name}"}
    )


@router.get("/mqm-xlsx/{project_id}", summary="导出 MQM 错误清单与裁决记录 (.xlsx)")
def download_mqm_xlsx(project_id: int, db: Session = Depends(get_db)):
    project, _, _, issue_list, _ = _get_project_data(project_id, db)
    buf = export_service.export_mqm_excel(issue_list)
    filename = f"{project.name}_mqm_issues.xlsx"
    encoded_name = urllib.parse.quote(filename)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_name}"}
    )


@router.get("/archive-zip/{project_id}", summary="导出全流程可复现归档包 (.zip)")
def download_archive_zip(project_id: int, db: Session = Depends(get_db)):
    project, seg_list, term_list, issue_list, report_dict = _get_project_data(project_id, db)
    buf = export_service.export_full_archive_zip(project.name, seg_list, term_list, issue_list, report_dict)
    filename = f"{project.name}_quality_archive.zip"
    encoded_name = urllib.parse.quote(filename)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_name}"}
    )
