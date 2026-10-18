"""
文档上传与解析 API
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.database import Document, Project, Segment
from app.services.document_parser import DocumentParser

router = APIRouter(prefix="/documents", tags=["文档管理"])

ALLOWED_TYPES = {".pdf", ".docx", ".doc", ".txt"}


def get_safe_filename(original_name: str) -> str:
    """生成安全的存储文件名"""
    ext = Path(original_name).suffix.lower()
    return f"{uuid.uuid4().hex}{ext}"


async def parse_document_task(
    file_path: str,
    document_id: int,
    project_id: int,
    db: Session,
):
    """后台任务：解析文档并创建段落"""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return

    try:
        doc.parse_status = "parsing"
        db.commit()

        parser = DocumentParser()
        result = parser.parse(file_path)
        segments_data = result["segments"]

        # 删除该文档的旧段落
        db.query(Segment).filter(
            Segment.document_id == document_id
        ).delete(synchronize_session=False)

        # 获取当前项目最大的 segment_counter，避免 ID 冲突
        from sqlalchemy import func
        max_order = db.query(func.max(Segment.order_index)).filter(
            Segment.project_id == project_id
        ).scalar() or 0

        # 重新生成 segment_id（确保项目内唯一）
        existing_count = db.query(func.count(Segment.id)).filter(
            Segment.project_id == project_id,
            Segment.document_id != document_id,
        ).scalar() or 0

        # 插入新段落
        segments = []
        for i, seg_data in enumerate(segments_data):
            # 重新编号确保全局唯一
            global_order = existing_count + i
            global_id = f"S{global_order + 1:03d}"

            segment = Segment(
                project_id=project_id,
                document_id=document_id,
                segment_id=global_id,
                section=seg_data.get("section", "正文"),
                section_level=seg_data.get("section_level", 0),
                order_index=global_order,
                source_text=seg_data["source_text"],
                status="pending",
            )
            segments.append(segment)

        db.bulk_save_objects(segments)

        # 更新文档状态
        doc.parse_status = "done"
        doc.word_count = result["word_count"]
        doc.segment_count = len(segments)

        # 更新项目段落统计
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            total = db.query(Segment).filter(Segment.project_id == project_id).count()
            project.total_segments = total
            project.status = "parsed"

        db.commit()

    except Exception as e:
        doc.parse_status = "error"
        doc.parse_error = str(e)
        db.commit()
        raise


@router.post("/upload/{project_id}", summary="上传文档到项目")
async def upload_document(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 验证文件类型
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式 {ext}，支持：{', '.join(ALLOWED_TYPES)}"
        )

    # 保存文件
    safe_name = get_safe_filename(file.filename)
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_name

    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    file_size = os.path.getsize(file_path)

    # 创建文档记录
    doc = Document(
        project_id=project_id,
        filename=safe_name,
        original_filename=file.filename,
        file_type=ext.lstrip("."),
        file_size=file_size,
        file_path=str(file_path),
        parse_status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 后台解析
    background_tasks.add_task(
        parse_document_task,
        str(file_path),
        doc.id,
        project_id,
        db,
    )

    return {
        "success": True,
        "message": "文件已上传，正在后台解析...",
        "document": {
            "id": doc.id,
            "filename": doc.original_filename,
            "file_type": doc.file_type,
            "file_size": file_size,
            "parse_status": doc.parse_status,
        },
    }


@router.get("/{document_id}", summary="获取文档信息")
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {
        "id": doc.id,
        "project_id": doc.project_id,
        "filename": doc.original_filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "parse_status": doc.parse_status,
        "parse_error": doc.parse_error,
        "word_count": doc.word_count,
        "segment_count": doc.segment_count,
        "created_at": doc.created_at,
    }


@router.get("/project/{project_id}", summary="获取项目所有文档")
def list_project_documents(project_id: int, db: Session = Depends(get_db)):
    docs = db.query(Document).filter(Document.project_id == project_id).all()
    return [
        {
            "id": d.id,
            "filename": d.original_filename,
            "file_type": d.file_type,
            "parse_status": d.parse_status,
            "word_count": d.word_count,
            "segment_count": d.segment_count,
            "created_at": d.created_at,
        }
        for d in docs
    ]
