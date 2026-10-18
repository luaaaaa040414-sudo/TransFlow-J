"""
导出归档服务 (Export Service)
生成学术出版要求的全流程材料：
1. 纯英文论文稿 (Word .docx)
2. 中英逐段对照审校稿 (Word .docx)
3. 核定术语与权威信源证据表 (Excel .xlsx)
4. MQM 错误清单与裁决记录 (Excel .xlsx)
5. 翻译全流程可复现归档包 (ZIP)
"""
import io
import os
import zipfile
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


class ExportService:

    def export_english_docx(self, project_name: str, segments: List[Dict[str, Any]]) -> io.BytesIO:
        """导出最终纯英文学术论文 Word 稿"""
        doc = Document()

        # 设置页面边距（标准学术论文 1 英寸）
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        # 标题
        title_p = doc.add_paragraph()
        title_run = title_p.add_run(project_name)
        title_run.font.name = "Times New Roman"
        title_run.font.size = Pt(18)
        title_run.font.bold = True
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph()

        # 按段落输出正文
        current_section = None
        for seg in segments:
            sec_name = seg.get("section") or "正文"
            sec_level = seg.get("section_level", 0)

            # 如果进入新的重要章节，添加章节标题
            if sec_name != current_section and sec_name not in ("正文", None):
                current_section = sec_name
                h = doc.add_paragraph()
                h_run = h.add_run(sec_name)
                h_run.font.name = "Times New Roman"
                h_run.font.size = Pt(14 if sec_level <= 1 else 12)
                h_run.font.bold = True

            text = seg.get("approved_text") or seg.get("translated_text") or ""
            if not text.strip():
                continue

            p = doc.add_paragraph()
            p_format = p.paragraph_format
            p_format.line_spacing = 1.5  # 1.5 倍行距
            p_format.space_after = Pt(6)

            run = p.add_run(text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf

    def export_bilingual_docx(self, project_name: str, segments: List[Dict[str, Any]]) -> io.BytesIO:
        """导出中英逐段双语对照审校 Word 稿（包含编号与修改对比）"""
        doc = Document()

        # 标题
        t = doc.add_heading(f"中英对照审校稿 - {project_name}", level=1)
        t.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # 添加表格 (四列：编号/章节 | 中文原文 | 英文定稿 | 状态与备注)
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        headers = ["编号/章节", "中文原文", "英文译文 (定稿)", "状态/FLAG"]
        for i, header_text in enumerate(headers):
            cell = hdr_cells[i]
            cell.text = header_text
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.bold = True
                    r.font.size = Pt(10)

        for seg in segments:
            row_cells = table.add_row().cells
            # 列 1: 编号 + 章节
            row_cells[0].text = f"[{seg.get('segment_id', '')}]\n{seg.get('section', '')}"
            # 列 2: 中文原文
            row_cells[1].text = seg.get("source_text", "")
            # 列 3: 英文译文
            final_text = seg.get("approved_text") or seg.get("translated_text") or "（未翻译）"
            row_cells[2].text = final_text
            # 列 4: 状态 & FLAG
            status = seg.get("status", "")
            flag_info = f"🚩 {seg.get('flag_reason')}" if seg.get("has_flag") else "正常"
            row_cells[3].text = f"状态: {status}\n{flag_info}"

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return buf

    def export_terminology_excel(self, terms: List[Dict[str, Any]]) -> io.BytesIO:
        """导出术语表及权威信源证据表 (Excel)"""
        wb = openpyxl.Workbook()
        ws_terms = wb.active
        ws_terms.title = "已确认术语表"

        # 表头
        headers = ["序号", "中文术语", "专业领域", "核定英文译法", "候选译法列表", "状态", "证据数"]
        ws_terms.append(headers)

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1A3A5C", end_color="1A3A5C", fill_type="solid")
        for col_idx in range(1, len(headers) + 1):
            cell = ws_terms.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        ws_evidence = wb.create_sheet(title="权威信源证据明细")
        ev_headers = ["术语", "信源等级", "信源类型", "信源名称", "支持译法", "发布日期", "信源 URL", "原文证据文本", "有效性"]
        ws_evidence.append(ev_headers)
        for col_idx in range(1, len(ev_headers) + 1):
            cell = ws_evidence.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = PatternFill(start_color="2D6A9F", end_color="2D6A9F", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")

        for idx, t in enumerate(terms, start=1):
            candidates_str = ", ".join(t.get("candidate_translations") or [])
            ev_list = t.get("evidence") or []
            ws_terms.append([
                idx,
                t.get("source_term", ""),
                t.get("domain", ""),
                t.get("confirmed_translation", "（未确认）"),
                candidates_str,
                t.get("status", ""),
                len(ev_list)
            ])

            for ev in ev_list:
                ws_evidence.append([
                    t.get("source_term", ""),
                    f"{ev.get('source_level')} 级",
                    ev.get("source_type", ""),
                    ev.get("source_name", ""),
                    ev.get("candidate_translation", ""),
                    ev.get("published_date", ""),
                    ev.get("source_url", ""),
                    ev.get("evidence_text", ""),
                    "有效" if ev.get("is_valid", True) else "无效"
                ])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    def export_mqm_excel(self, issues: List[Dict[str, Any]]) -> io.BytesIO:
        """导出 MQM 错误清单与人工裁决记录 (Excel)"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "MQM 错误清单与裁决"

        headers = ["ID", "段落编号", "严重程度", "错误大类", "子类型", "检测模型", "原文片断", "译文片断", "问题说明", "建议修改", "依据", "人工裁决", "裁决理由"]
        ws.append(headers)

        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="8C1D40", end_color="8C1D40", fill_type="solid")
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        for issue in issues:
            ws.append([
                issue.get("id"),
                issue.get("segment_id", ""),
                issue.get("severity", ""),
                issue.get("error_type", ""),
                issue.get("error_subtype", ""),
                issue.get("detected_by", ""),
                issue.get("source_span", ""),
                issue.get("translation_span", ""),
                issue.get("explanation", ""),
                issue.get("suggested_revision", ""),
                issue.get("evidence", ""),
                issue.get("human_status", ""),
                issue.get("human_decision_text", "")
            ])

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    def export_full_archive_zip(
        self,
        project_name: str,
        segments: List[Dict[str, Any]],
        terms: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        quality_report: Optional[Dict[str, Any]] = None,
    ) -> io.BytesIO:
        """打包导出翻译全流程可复现归档包 (ZIP)"""
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. 纯英文稿
            doc_en = self.export_english_docx(project_name, segments)
            zf.writestr(f"01_英文论文稿_{project_name}.docx", doc_en.getvalue())

            # 2. 中英对照审校稿
            doc_bi = self.export_bilingual_docx(project_name, segments)
            zf.writestr(f"02_中英逐段对照审校稿_{project_name}.docx", doc_bi.getvalue())

            # 3. 术语与信源证据
            excel_terms = self.export_terminology_excel(terms)
            zf.writestr(f"03_术语及权威信源证据表_{project_name}.xlsx", excel_terms.getvalue())

            # 4. MQM 错误与裁决清单
            excel_mqm = self.export_mqm_excel(issues)
            zf.writestr(f"04_MQM质量评审与裁决记录_{project_name}.xlsx", excel_mqm.getvalue())

            # 5. 质量指标与审计报告 (JSON)
            audit_metadata = {
                "project_name": project_name,
                "exported_at": datetime.utcnow().isoformat(),
                "total_segments": len(segments),
                "translated_segments": sum(1 for s in segments if s.get("translated_text")),
                "approved_segments": sum(1 for s in segments if s.get("status") == "approved"),
                "total_mqm_issues": len(issues),
                "quality_report": quality_report or {},
                "audit_statement": "所有翻译段落、术语信源、多模型互审记录及人工裁决均完整保留并具备复现性。"
            }
            zf.writestr(f"05_翻译质量保障审计归档_{project_name}.json", json.dumps(audit_metadata, ensure_ascii=False, indent=2))

        zip_buf.seek(0)
        return zip_buf


export_service = ExportService()
