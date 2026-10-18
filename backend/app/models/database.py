"""
数据库模型定义 - SQLAlchemy ORM
包含所有核心业务表
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime
import enum


class Base(DeclarativeBase):
    pass


# ============================================================
# 枚举类型
# ============================================================

class ProjectStatus(str, enum.Enum):
    CREATED = "created"
    PARSING = "parsing"
    PARSED = "parsed"
    TRANSLATING = "translating"
    TRANSLATED = "translated"
    PROOFREADING = "proofreading"
    COMPLETED = "completed"


class SegmentStatus(str, enum.Enum):
    PENDING = "pending"
    TRANSLATING = "translating"
    TRANSLATED = "translated"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    FLAGGED = "flagged"


class TermStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    REJECTED = "rejected"


class IssueSeverity(str, enum.Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    NEUTRAL = "neutral"


class IssueStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    MODIFIED = "modified"


def enum_vals(cls):
    return [e.value for e in cls]


# ============================================================
# 论文项目表
# ============================================================

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, comment="项目名称（通常是论文标题）")
    description = Column(Text, nullable=True, comment="项目描述")
    source_language = Column(String(10), default="zh", comment="源语言")
    target_language = Column(String(10), default="en", comment="目标语言")
    domain = Column(String(200), nullable=True, comment="学科领域")
    status = Column(String(50), default="created")

    # 期刊关联
    journal_id = Column(Integer, ForeignKey("journals.id"), nullable=True)
    article_type = Column(String(100), nullable=True, comment="文章类型：研究论文/综述/短文等")

    # 翻译配置
    translation_provider = Column(String(100), nullable=True, comment="翻译模型提供商")
    translation_model = Column(String(200), nullable=True, comment="翻译模型标识")

    # 统计
    total_segments = Column(Integer, default=0)
    translated_segments = Column(Integer, default=0)
    approved_segments = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    segments = relationship("Segment", back_populates="project", cascade="all, delete-orphan")
    terminology = relationship("TerminologyEntry", back_populates="project", cascade="all, delete-orphan")
    quality_reports = relationship("QualityReport", back_populates="project", cascade="all, delete-orphan")
    journal = relationship("Journal", back_populates="projects")


# ============================================================
# 上传文档表
# ============================================================

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False, comment="pdf/docx/txt")
    file_size = Column(Integer, nullable=True, comment="字节数")
    file_path = Column(String(1000), nullable=False)
    parse_status = Column(String(50), default="pending", comment="pending/parsing/done/error")
    parse_error = Column(Text, nullable=True)
    word_count = Column(Integer, default=0, comment="中文字符数")
    segment_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="documents")


# ============================================================
# 段落表（核心翻译单位）
# ============================================================

class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)

    segment_id = Column(String(20), nullable=False, index=True, comment="如 S001")
    section = Column(String(200), nullable=True, comment="所属章节：摘要/引言/方法等")
    section_level = Column(Integer, default=0, comment="章节层级 0=正文 1=一级标题 2=二级标题")
    order_index = Column(Integer, nullable=False, comment="段落顺序")

    source_text = Column(Text, nullable=False, comment="中文原文")
    translated_text = Column(Text, nullable=True, comment="当前英文译文")
    initial_translation = Column(Text, nullable=True, comment="初始机器译文（保留原始）")
    approved_text = Column(Text, nullable=True, comment="人工定稿译文")
    status = Column(String(50), default="pending")
    has_flag = Column(Boolean, default=False, comment="是否有 FLAG 标记")
    flag_reason = Column(Text, nullable=True, comment="FLAG 原因")

    # 翻译元数据
    translation_model = Column(String(200), nullable=True)
    translation_provider = Column(String(100), nullable=True)
    translated_at = Column(DateTime, nullable=True)

    # 数字检查结果
    numbers_verified = Column(Boolean, default=False)
    numbers_issues = Column(JSON, nullable=True, comment="数字一致性问题列表")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="segments")
    issues = relationship("ReviewIssue", back_populates="segment", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="segment", cascade="all, delete-orphan")


# ============================================================
# 术语表
# ============================================================

class TerminologyEntry(Base):
    __tablename__ = "terminology"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    source_term = Column(String(500), nullable=False, comment="中文术语")
    domain = Column(String(200), nullable=True, comment="专业领域")
    candidate_translations = Column(JSON, nullable=True, comment="候选英文译法列表")
    confirmed_translation = Column(String(500), nullable=True, comment="确认采用的英文译法")

    status = Column(String(50), default="pending")
    notes = Column(Text, nullable=True, comment="备注")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="terminology")
    evidence = relationship("SourceEvidence", back_populates="term", cascade="all, delete-orphan")


# ============================================================
# 权威信源证据表
# ============================================================

class SourceEvidence(Base):
    __tablename__ = "source_evidence"

    id = Column(Integer, primary_key=True, index=True)
    term_id = Column(Integer, ForeignKey("terminology.id"), nullable=False)

    source_level = Column(Integer, nullable=False, comment="信源等级 1=最权威")
    source_type = Column(String(100), nullable=True, comment="官方词典/行业标准/专业期刊等")
    source_name = Column(String(500), nullable=True, comment="来源名称")
    source_url = Column(String(2000), nullable=True, comment="来源 URL")
    evidence_text = Column(Text, nullable=True, comment="原文证据片段")
    candidate_translation = Column(String(500), nullable=True, comment="该信源支持的译法")
    published_date = Column(String(50), nullable=True, comment="发布/更新日期（可获得时）")

    verified_by = Column(String(200), nullable=True, comment="核验者")
    verified_at = Column(DateTime, nullable=True)
    is_valid = Column(Boolean, default=True, comment="该证据是否有效")

    created_at = Column(DateTime, default=datetime.utcnow)

    term = relationship("TerminologyEntry", back_populates="evidence")


# ============================================================
# 期刊表
# ============================================================

class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False, comment="期刊名称")
    abbreviation = Column(String(100), nullable=True, comment="期刊缩写")
    publisher = Column(String(300), nullable=True, comment="出版商")
    issn = Column(String(20), nullable=True)
    homepage_url = Column(String(2000), nullable=True, comment="期刊主页")
    author_guide_url = Column(String(2000), nullable=True, comment="官方作者指南 URL")
    impact_factor = Column(Float, nullable=True)
    domain = Column(String(300), nullable=True, comment="学科领域")

    # 语言规范
    english_variant = Column(String(20), default="American", comment="American/British")
    article_types = Column(JSON, nullable=True, comment="支持的文章类型")

    # 摘要和正文要求
    abstract_word_limit = Column(Integer, nullable=True)
    body_word_limit = Column(Integer, nullable=True)

    # 风格规则（JSON 存储）
    style_rules = Column(JSON, nullable=True, comment="从官方指南归纳的风格规则")

    # 引用格式
    citation_style = Column(String(100), nullable=True, comment="APA/Vancouver/Chicago 等")

    guide_verified_date = Column(String(50), nullable=True, comment="指南核验日期")
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = relationship("Project", back_populates="journal")


# ============================================================
# 模型配置表
# ============================================================

class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="用户自定义名称")
    provider = Column(String(100), nullable=False, comment="openai/anthropic/google/deepseek/custom")
    model_id = Column(String(300), nullable=False, comment="实际模型标识")
    api_base_url = Column(String(1000), nullable=True)

    # 能力说明
    capabilities = Column(JSON, nullable=True, comment="能力标签：翻译/长文/推理/结构化输出")
    context_window = Column(Integer, nullable=True, comment="上下文窗口 token 数")
    supports_json_mode = Column(Boolean, default=False)

    # 费用（用户自行填写估算）
    cost_per_1k_input = Column(Float, nullable=True, comment="每千输入 token 费用（USD）")
    cost_per_1k_output = Column(Float, nullable=True, comment="每千输出 token 费用（USD）")

    use_for_translation = Column(Boolean, default=True)
    use_for_proofreading = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# 校对问题表（MQM 错误记录）
# ============================================================

class ReviewIssue(Base):
    __tablename__ = "review_issues"

    id = Column(Integer, primary_key=True, index=True)
    segment_id_fk = Column(Integer, ForeignKey("segments.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # 错误标注
    error_type = Column(String(100), nullable=False, comment="MQM 错误类型：Accuracy/Fluency/Terminology/Style/Punctuation")
    error_subtype = Column(String(100), nullable=True, comment="错误子类型")
    severity = Column(String(50), nullable=False, default="minor")

    # 定位信息
    source_span = Column(Text, nullable=True, comment="原文中的相关片段")
    translation_span = Column(Text, nullable=True, comment="译文中的相关片段")

    # 内容
    explanation = Column(Text, nullable=False, comment="问题说明")
    suggested_revision = Column(Text, nullable=True, comment="建议修改后的译文")
    evidence = Column(Text, nullable=True, comment="对应依据（术语、原文等）")

    # 来源
    detected_by = Column(String(200), nullable=True, comment="检测者：模型名称或 rule_checker")
    detection_model = Column(String(300), nullable=True, comment="具体模型版本")

    # 人工裁决
    human_status = Column(String(50), default="pending")
    human_decision_text = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decided_by = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    segment = relationship("Segment", back_populates="issues")


# ============================================================
# 人工裁决记录表
# ============================================================

class Decision(Base):
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True)
    segment_id_fk = Column(Integer, ForeignKey("segments.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    action = Column(String(100), nullable=False, comment="edit/approve/flag/revert")
    before_text = Column(Text, nullable=True, comment="修改前译文")
    after_text = Column(Text, nullable=True, comment="修改后译文")
    reason = Column(Text, nullable=True, comment="修改理由")
    operator = Column(String(200), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    segment = relationship("Segment", back_populates="decisions")


# ============================================================
# 质量报告表
# ============================================================

class QualityReport(Base):
    __tablename__ = "quality_reports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    report_type = Column(String(50), default="full", comment="full/segment/terminology")

    # 统计指标
    total_segments = Column(Integer, default=0)
    translated_segments = Column(Integer, default=0)
    approved_segments = Column(Integer, default=0)
    flagged_segments = Column(Integer, default=0)

    total_issues = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    major_issues = Column(Integer, default=0)
    minor_issues = Column(Integer, default=0)
    resolved_issues = Column(Integer, default=0)

    # 关键质量指标
    number_errors = Column(Integer, default=0, comment="数字一致性错误数")
    terminology_consistency_rate = Column(Float, nullable=True, comment="术语一致率 0-1")
    adoption_rate = Column(Float, nullable=True, comment="校对建议采纳率 0-1")
    human_edit_rate = Column(Float, nullable=True, comment="人工修改率 0-1")

    # 检查范围说明
    check_scope = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # 完整报告数据（JSON）
    report_data = Column(JSON, nullable=True)

    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(String(200), nullable=True)

    project = relationship("Project", back_populates="quality_reports")
