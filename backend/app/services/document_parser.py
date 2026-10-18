"""
文档解析服务
支持 PDF、DOCX、TXT 格式
提取文本、识别章节结构、生成稳定段落编号 S001, S002...
"""
import os
import re
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================
# 段落数据结构
# ============================================================

class ParsedSegment:
    """解析后的段落"""
    def __init__(
        self,
        segment_id: str,
        section: str,
        section_level: int,
        order_index: int,
        source_text: str,
    ):
        self.segment_id = segment_id
        self.section = section
        self.section_level = section_level
        self.order_index = order_index
        self.source_text = source_text

    def to_dict(self) -> Dict:
        return {
            "segment_id": self.segment_id,
            "section": self.section,
            "section_level": self.section_level,
            "order_index": self.order_index,
            "source_text": self.source_text,
            "translated_text": "",
            "status": "pending",
        }


# ============================================================
# 章节识别规则
# ============================================================

# 常见中文学术论文章节标题
SECTION_PATTERNS = [
    # 摘要
    (r"^摘\s*要$", "摘要", 1),
    (r"^Abstract$", "Abstract", 1),
    # 关键词
    (r"^关键词", "关键词", 1),
    (r"^Keywords", "Keywords", 1),
    # 引言/绪论
    (r"^[1１一][\.\s、]?\s*(引言|绪论|前言|介绍)", "引言", 1),
    (r"^\d+\s+引言", "引言", 1),
    # 文献综述
    (r"^[2２二][\.\s、]?\s*文献综述", "文献综述", 1),
    # 研究方法
    (r"^[\d一二三四五六七八九十]+[\.\s、]?\s*(研究方法|方法|实验方法|材料与方法|方法论)", "方法", 1),
    # 实验/数据
    (r"^[\d一二三四五六七八九十]+[\.\s、]?\s*(实验|数据|数据集|实验设计)", "实验", 1),
    # 结果
    (r"^[\d一二三四五六七八九十]+[\.\s、]?\s*(结果|实验结果|研究结果)", "结果", 1),
    # 讨论
    (r"^[\d一二三四五六七八九十]+[\.\s、]?\s*(讨论|分析与讨论)", "讨论", 1),
    # 结论
    (r"^[\d一二三四五六七八九十]+[\.\s、]?\s*(结论|总结|结语|结束语)", "结论", 1),
    # 参考文献
    (r"^参考文献", "参考文献", 1),
    (r"^References", "References", 1),
    # 致谢
    (r"^致谢", "致谢", 1),
    # 附录
    (r"^附录", "附录", 1),
    # 通用数字章节（如 1.1 子节）
    (r"^\d+\.\d+\s+\S", None, 2),
    (r"^\d+\.\d+\.\d+\s+\S", None, 3),
]


def detect_section(text: str) -> Tuple[Optional[str], int]:
    """
    判断一段文字是否是章节标题
    返回 (section_name, level) 或 (None, 0)
    """
    stripped = text.strip()
    if len(stripped) > 100:  # 标题通常不会太长
        return None, 0

    for pattern, section_name, level in SECTION_PATTERNS:
        if re.match(pattern, stripped, re.IGNORECASE):
            name = section_name or stripped
            return name, level

    return None, 0


def is_reference_line(text: str) -> bool:
    """检查是否是参考文献条目（通常以 [数字] 开头）"""
    return bool(re.match(r"^\[\d+\]", text.strip()))


def clean_text(text: str) -> str:
    """基础文本清洗"""
    # 去除多余空白
    text = re.sub(r"\s+", " ", text).strip()
    # 去除页眉页脚常见标记（简单规则）
    return text


# ============================================================
# 中文字符计数
# ============================================================

def count_chinese_chars(text: str) -> int:
    """统计中文字符数"""
    return len(re.findall(r"[\u4e00-\u9fff]", text))


# ============================================================
# 解析器主类
# ============================================================

class DocumentParser:

    def __init__(self):
        self.segments: List[ParsedSegment] = []
        self.current_section = "正文"
        self.current_section_level = 0
        self.segment_counter = 0
        self.word_count = 0

    def _next_segment_id(self) -> str:
        self.segment_counter += 1
        return f"S{self.segment_counter:03d}"

    def _add_segment(self, text: str, section: str = None, level: int = 0):
        """添加一个有效段落"""
        text = clean_text(text)
        if not text or len(text) < 2:
            return

        # 检查是否是章节标题
        detected_section, detected_level = detect_section(text)
        if detected_section:
            self.current_section = detected_section
            self.current_section_level = detected_level

        seg = ParsedSegment(
            segment_id=self._next_segment_id(),
            section=section or self.current_section,
            section_level=level or self.current_section_level,
            order_index=self.segment_counter,
            source_text=text,
        )
        self.segments.append(seg)
        self.word_count += count_chinese_chars(text)

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """将文本块拆分为段落"""
        raw_lines = text.split("\n")
        non_empty = [l.strip() for l in raw_lines if l.strip()]
        empty_count = sum(1 for l in raw_lines if not l.strip())

        # 如果几乎没有空行（例如单行分段的文稿或讲稿），直接按非空行分段
        if empty_count < max(2, len(non_empty) * 0.2):
            return non_empty

        # 否则按空行合并多行段落
        paragraphs = []
        current = []
        for line in raw_lines:
            stripped = line.strip()
            if not stripped:
                if current:
                    para = " ".join(current).strip()
                    if para:
                        paragraphs.append(para)
                    current = []
            else:
                current.append(stripped)

        if current:
            para = " ".join(current).strip()
            if para:
                paragraphs.append(para)

        return paragraphs

    # ---- PDF 解析 ----

    def parse_pdf(self, file_path: str) -> List[Dict]:
        """解析 PDF 文件"""
        try:
            from pypdf import PdfReader
        except ImportError:
            raise RuntimeError("pypdf 未安装，请运行 pip install pypdf")

        try:
            reader = PdfReader(file_path)
            full_text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n\n"

            if not full_text.strip():
                logger.warning(f"PDF 文本提取为空: {file_path}")
                return []

            paragraphs = self._split_into_paragraphs(full_text)
            for para in paragraphs:
                self._add_segment(para)

        except Exception as e:
            logger.error(f"PDF 解析失败: {e}")
            raise

        return [s.to_dict() for s in self.segments]

    # ---- DOCX 解析 ----

    def parse_docx(self, file_path: str) -> List[Dict]:
        """解析 Word DOCX 文件，保留段落结构"""
        try:
            from docx import Document
        except ImportError:
            raise RuntimeError("python-docx 未安装")

        try:
            doc = Document(file_path)

            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue

                # 检查样式名判断标题级别
                style_name = para.style.name if para.style else ""
                level = 0
                if "Heading 1" in style_name or "标题 1" in style_name:
                    level = 1
                elif "Heading 2" in style_name or "标题 2" in style_name:
                    level = 2
                elif "Heading 3" in style_name or "标题 3" in style_name:
                    level = 3

                self._add_segment(text, level=level)

            # 解析表格（标记为特殊内容）
            for i, table in enumerate(doc.tables):
                table_texts = []
                for row in table.rows:
                    row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                    if row_texts:
                        table_texts.append(" | ".join(row_texts))
                if table_texts:
                    table_text = f"[表格 {i+1}] " + " / ".join(table_texts[:3])
                    self._add_segment(table_text, section="表格")

        except Exception as e:
            logger.error(f"DOCX 解析失败: {e}")
            raise

        return [s.to_dict() for s in self.segments]

    # ---- TXT 解析 ----

    def parse_txt(self, file_path: str) -> List[Dict]:
        """解析纯文本文件"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"TXT 解析失败: {e}")
            raise

        paragraphs = self._split_into_paragraphs(content)
        for para in paragraphs:
            self._add_segment(para)

        return [s.to_dict() for s in self.segments]

    # ---- 统一入口 ----

    def parse(self, file_path: str) -> Dict:
        """
        统一解析入口
        根据文件扩展名选择解析器
        返回 {"segments": [...], "word_count": N, "segment_count": N}
        """
        ext = Path(file_path).suffix.lower()

        if ext == ".pdf":
            segments = self.parse_pdf(file_path)
        elif ext in (".docx", ".doc"):
            segments = self.parse_docx(file_path)
        elif ext == ".txt":
            segments = self.parse_txt(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

        return {
            "segments": segments,
            "word_count": self.word_count,
            "segment_count": len(segments),
        }
