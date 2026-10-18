"""
Pydantic Schemas - 请求/响应数据验证
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


# ============================================================
# 通用
# ============================================================

class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int


class APIResponse(BaseModel):
    success: bool = True
    message: str = "操作成功"
    data: Any = None


# ============================================================
# 项目
# ============================================================

class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=500, description="项目名称")
    description: Optional[str] = None
    domain: Optional[str] = None
    journal_id: Optional[int] = None
    article_type: Optional[str] = None
    translation_provider: Optional[str] = "openai"
    translation_model: Optional[str] = "gpt-4o"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    journal_id: Optional[int] = None
    article_type: Optional[str] = None
    translation_provider: Optional[str] = None
    translation_model: Optional[str] = None
    status: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    domain: Optional[str]
    status: str
    journal_id: Optional[int]
    article_type: Optional[str]
    translation_provider: Optional[str]
    translation_model: Optional[str]
    total_segments: int
    translated_segments: int
    approved_segments: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 段落
# ============================================================

class SegmentResponse(BaseModel):
    id: int
    segment_id: str
    section: Optional[str]
    section_level: int
    order_index: int
    source_text: str
    translated_text: Optional[str]
    initial_translation: Optional[str]
    approved_text: Optional[str]
    status: str
    has_flag: bool
    flag_reason: Optional[str]
    translation_model: Optional[str]
    numbers_verified: bool
    numbers_issues: Optional[List[Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SegmentUpdate(BaseModel):
    translated_text: Optional[str] = None
    approved_text: Optional[str] = None
    status: Optional[str] = None
    has_flag: Optional[bool] = None
    flag_reason: Optional[str] = None


class TranslationRequest(BaseModel):
    segment_ids: Optional[List[int]] = None  # None = 翻译全部
    provider: Optional[str] = None
    model: Optional[str] = None
    journal_id: Optional[int] = None


# ============================================================
# 术语
# ============================================================

class TermCreate(BaseModel):
    source_term: str
    domain: Optional[str] = None
    notes: Optional[str] = None


class TermUpdate(BaseModel):
    confirmed_translation: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class TermResponse(BaseModel):
    id: int
    source_term: str
    domain: Optional[str]
    candidate_translations: Optional[List[Any]]
    confirmed_translation: Optional[str]
    status: str
    notes: Optional[str]
    created_at: datetime
    evidence: List[Any] = []
    cards: Optional[List[Any]] = []
    decomposition: Optional[List[Any]] = None
    research_summary: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class EvidenceCreate(BaseModel):
    source_level: int = Field(..., ge=1, le=5)
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    evidence_text: Optional[str] = None
    candidate_translation: Optional[str] = None
    published_date: Optional[str] = None


class EvidenceResponse(BaseModel):
    id: int
    source_level: int
    source_type: Optional[str]
    source_name: Optional[str]
    source_url: Optional[str]
    evidence_text: Optional[str]
    candidate_translation: Optional[str]
    published_date: Optional[str]
    verified_at: Optional[datetime]
    is_valid: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 期刊
# ============================================================

class JournalCreate(BaseModel):
    name: str
    abbreviation: Optional[str] = None
    publisher: Optional[str] = None
    issn: Optional[str] = None
    homepage_url: Optional[str] = None
    author_guide_url: Optional[str] = None
    domain: Optional[str] = None
    english_variant: str = "American"
    article_types: Optional[List[str]] = None
    abstract_word_limit: Optional[int] = None
    body_word_limit: Optional[int] = None
    style_rules: Optional[Dict] = None
    citation_style: Optional[str] = None


class JournalResponse(BaseModel):
    id: int
    name: str
    abbreviation: Optional[str]
    publisher: Optional[str]
    issn: Optional[str]
    homepage_url: Optional[str]
    author_guide_url: Optional[str]
    impact_factor: Optional[float]
    domain: Optional[str]
    english_variant: str
    article_types: Optional[List[str]]
    abstract_word_limit: Optional[int]
    body_word_limit: Optional[int]
    style_rules: Optional[Dict]
    citation_style: Optional[str]
    guide_verified_date: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# 模型配置
# ============================================================

class ModelConfigCreate(BaseModel):
    name: str
    provider: str
    model_id: str
    api_base_url: Optional[str] = None
    capabilities: Optional[List[str]] = None
    context_window: Optional[int] = None
    supports_json_mode: bool = False
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    use_for_translation: bool = True
    use_for_proofreading: bool = True


class ModelConfigResponse(BaseModel):
    id: int
    name: str
    provider: str
    model_id: str
    api_base_url: Optional[str]
    capabilities: Optional[List[str]]
    context_window: Optional[int]
    supports_json_mode: bool
    cost_per_1k_input: Optional[float]
    cost_per_1k_output: Optional[float]
    use_for_translation: bool
    use_for_proofreading: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeysSchema(BaseModel):
    openai_api_key: Optional[str] = ""
    openai_base_url: Optional[str] = "https://api.openai.com/v1"
    deepseek_api_key: Optional[str] = ""
    deepseek_base_url: Optional[str] = "https://api.deepseek.com/v1"
    anthropic_api_key: Optional[str] = ""
    custom_api_key: Optional[str] = ""
    custom_base_url: Optional[str] = ""


class TestProviderRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


# ============================================================
# 校对问题
# ============================================================

class IssueResponse(BaseModel):
    id: int
    segment_id_fk: int
    error_type: str
    error_subtype: Optional[str]
    severity: str
    source_span: Optional[str]
    translation_span: Optional[str]
    explanation: str
    suggested_revision: Optional[str]
    evidence: Optional[str]
    detected_by: Optional[str]
    detection_model: Optional[str]
    human_status: str
    human_decision_text: Optional[str]
    decided_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class IssueDecision(BaseModel):
    human_status: str  # accepted/rejected/modified
    human_decision_text: Optional[str] = None
    final_text: Optional[str] = None  # 如果是 modified，提供最终译文


# ============================================================
# 质量报告
# ============================================================

class QualityReportResponse(BaseModel):
    id: int
    project_id: int
    report_type: str
    total_segments: int
    translated_segments: int
    approved_segments: int
    flagged_segments: int
    total_issues: int
    critical_issues: int
    major_issues: int
    minor_issues: int
    resolved_issues: int
    number_errors: int
    terminology_consistency_rate: Optional[float]
    adoption_rate: Optional[float]
    human_edit_rate: Optional[float]
    check_scope: Optional[str]
    notes: Optional[str]
    generated_at: datetime

    class Config:
        from_attributes = True
