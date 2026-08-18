from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel, Field


# ─── Domain models ────────────────────────────────────────────────────────────

class CodebookVariable(BaseModel):
    variable_name: str
    description: str
    dType: Optional[str] = None
    unit: Optional[str] = None
    categories: Optional[str] = None
    unit_example: Optional[str] = None


class StudyVariable(BaseModel):
    variable_name: str
    description: Optional[str] = None
    target_recommendations: Optional[list[str]] = None
    target_distances: Optional[list[float]] = None
    PID_recommendations: Optional[list[str]] = None
    PID_distances: Optional[list[float]] = None
    date_recommendations: Optional[list[str]] = None
    date_distances: Optional[list[float]] = None


class Study(BaseModel):
    name: str
    variable_count: int
    has_example_data: bool = False
    has_context_pdf: bool = False
    has_results: bool = False
    status: Literal["uploaded", "initialised", "mapping", "complete"]


class MappingRecord(BaseModel):
    study_var: str
    codebook_var: Optional[str] = None
    confidence: Optional[str] = None
    notes: Optional[str] = None
    marked: Literal[
        "To do", "Successfully mapped", "Marked to reconsider", "Marked unmappable"
    ] = "To do"
    transformation_instructions: Optional[str] = None
    transformation_type: Optional[Literal["Direct", "Categorical"]] = None
    source_dtype: Optional[str] = None
    target_dtype: Optional[str] = None
    patient_id_var: Optional[str] = None
    patient_id_confidence: Optional[str] = None
    date_var: Optional[str] = None
    date_confidence: Optional[str] = None
    # Computed on-the-fly for the list endpoint (not persisted to CSV)
    best_confidence: Optional[int] = None


class ProviderSlot(BaseModel):
    """A single provider+model configuration for one role (chat or embedding)."""
    provider: Literal["ollama", "vllm", "openai", "anthropic", "azure_openai"]
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    azure_api_version: Optional[str] = None
    azure_deployment: Optional[str] = None


class AIConfig(BaseModel):
    chat: ProviderSlot
    embedding: Optional[ProviderSlot] = None
    request_timeout: int = 30


# ─── Request models ───────────────────────────────────────────────────────────

class InitialiseRequest(BaseModel):
    ai_config: AIConfig
    init_prompt: str = (
        "As an AI, you're given the task of translating short variable names "
        "from a public health study into the most likely full variable name."
    )
    force_rerun: bool = False


class MappingUpdateRequest(BaseModel):
    codebook_var: Optional[str] = None
    marked: Literal[
        "To do", "Successfully mapped", "Marked to reconsider", "Marked unmappable"
    ] = "To do"
    notes: Optional[str] = Field(None, max_length=500)
    transformation_type: Optional[Literal["Direct", "Categorical"]] = None
    transformation_instructions: Optional[str] = Field(None, max_length=500)
    source_dtype: Optional[str] = None
    target_dtype: Optional[str] = None
    patient_id_var: Optional[str] = None
    date_var: Optional[str] = None
    operator_name: Optional[str] = Field(None, max_length=100)


class TransformationPreviewRequest(BaseModel):
    example_data: list[str]
    transformation_type: Literal["Direct", "Categorical"]
    transformation_instructions: str
    source_dtype: str = "float"
    target_dtype: str = "float"


class ValidateExpressionRequest(BaseModel):
    expression: str


class TransformedDataRequest(BaseModel):
    studies: list[str]


# ─── Response models ──────────────────────────────────────────────────────────

class CodebookUploadResponse(BaseModel):
    status: str
    row_count: int
    columns: list[str]
    warnings: list[str]


class StudyUploadResponse(BaseModel):
    study_name: str
    variable_count: int
    has_example_data: bool
    has_context_pdf: bool
    warnings: list[str]


class TransformationPreviewItem(BaseModel):
    original: str
    transformed: str


class TransformationPreviewResponse(BaseModel):
    preview: list[TransformationPreviewItem]
    transformed_count: int
    blank_count: int
    valid: bool
    error: Optional[str] = None


class ValidateExpressionResponse(BaseModel):
    valid: bool
    message: str


class RecommendationItem(BaseModel):
    codebook_var: str
    description: str
    confidence: int


class PIDRecommendationItem(BaseModel):
    variable_name: str
    confidence: int


class VariableDetailResponse(BaseModel):
    variable: StudyVariable
    example_data: list[str]
    recommendations: list[RecommendationItem]
    pid_recommendations: list[PIDRecommendationItem]
    date_recommendations: list[PIDRecommendationItem]
    existing_mapping: MappingRecord
    already_used_codebook_vars: list[str]


class MappingsListResponse(BaseModel):
    study: str
    total: int
    mapped: int
    progress: float
    records: list[MappingRecord]


class StudyInitStatus(BaseModel):
    name: str
    descriptions_generated: bool
    embeddings_ready: bool
    recommendations_ready: bool
    pid_date_ready: bool


class InitialiseStatusResponse(BaseModel):
    codebook_embedded: bool
    studies: list[StudyInitStatus]


class ProviderInfo(BaseModel):
    id: str
    name: str
    requires_api_key: bool
    requires_base_url: bool = False
    default_base_url: Optional[str] = None
    supports_embeddings: bool
    default_chat_model: Optional[str] = None
    default_embedding_model: Optional[str] = None
    api_key_pattern: Optional[str] = None
    requires_deployment: Optional[bool] = None
    note: Optional[str] = None


class SlotTestResult(BaseModel):
    connected: bool
    message: str


class AITestResponse(BaseModel):
    connected: bool
    chat: SlotTestResult
    embedding: Optional[SlotTestResult] = None


class OllamaModelsResponse(BaseModel):
    models: list[str]
