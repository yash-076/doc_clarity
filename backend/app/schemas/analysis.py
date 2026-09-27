import uuid
from typing import Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict


class AnalysisRequest(BaseModel):
    """Schema for requesting document analysis."""
    force_refresh: bool = Field(
        default=False,
        description="If true, forces re-generation of analysis even if cached analysis exists."
    )


class Citation(BaseModel):
    """Traceable citation pointing to specific document chunk and page."""
    chunk_id: uuid.UUID = Field(..., description="Unique UUID of the source document chunk.")
    page_number: Optional[int] = Field(default=None, description="Page number where finding was extracted.")
    section: Optional[str] = Field(default=None, description="Detected section title or header.")

    model_config = ConfigDict(from_attributes=True)


class KeyPoint(BaseModel):
    """Core key point or finding in the document."""
    title: str = Field(..., description="Short title of the key finding.")
    description: str = Field(..., description="Detailed description of the finding.")
    citations: List[Citation] = Field(default_factory=list, description="Traceable source citations.")


class ImportantDate(BaseModel):
    """Explicit date or deadline mentioned in the document."""
    description: str = Field(..., description="Context of the date (e.g., Policy Start Date, Filing Deadline).")
    date: Optional[str] = Field(default=None, description="Explicit date string or relative period.")
    citations: List[Citation] = Field(default_factory=list, description="Traceable source citations.")


class FinancialTerm(BaseModel):
    """Explicit monetary term, fee, limit, or amount."""
    description: str = Field(..., description="Context of the financial term (e.g., Annual Premium, Deductible).")
    amount: Optional[str] = Field(default=None, description="Monetary amount with currency and frequency.")
    citations: List[Citation] = Field(default_factory=list, description="Traceable source citations.")


class Obligation(BaseModel):
    """Explicit responsibility or duty assigned to a party."""
    party: str = Field(..., description="Responsible party (e.g., Policyholder, Tenant, Insurer, Patient).")
    description: str = Field(..., description="Description of the obligation or requirement.")
    citations: List[Citation] = Field(default_factory=list, description="Traceable source citations.")


class Exclusion(BaseModel):
    """Explicit exclusion, non-covered scenario, or restriction."""
    description: str = Field(..., description="Detailed description of the exclusion or limitation.")
    citations: List[Citation] = Field(default_factory=list, description="Traceable source citations.")


class AttentionItem(BaseModel):
    """Item or clause requiring user attention or review."""
    title: str = Field(..., description="Short summary of the attention item.")
    description: str = Field(..., description="Factual description of the concerning or important clause.")
    category: Literal[
        "deadline",
        "financial",
        "exclusion",
        "liability",
        "termination",
        "waiting_period",
        "restriction",
        "missing_information",
        "unusual_condition",
        "other"
    ] = Field(..., description="Category of the attention item.")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity level based on documented criteria.")
    citations: List[Citation] = Field(default_factory=list, description="Traceable source citations.")


class DocumentAnalysisResponse(BaseModel):
    """Structured response for automatic document analysis."""
    id: uuid.UUID = Field(..., description="Unique ID of the analysis record.")
    document_id: uuid.UUID = Field(..., description="Target document ID.")
    document_type: str = Field(..., description="Domain type of document (legal, insurance, medical, other).")
    summary: str = Field(..., description="Executive summary (150-300 words).")
    key_points: List[KeyPoint] = Field(default_factory=list)
    important_dates: List[ImportantDate] = Field(default_factory=list)
    financial_terms: List[FinancialTerm] = Field(default_factory=list)
    obligations: List[Obligation] = Field(default_factory=list)
    exclusions: List[Exclusion] = Field(default_factory=list)
    attention_items: List[AttentionItem] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = Field(default="high")
    analysis_version: int = Field(default=1)
    embedding_model: Optional[str] = Field(default=None)
    llm_model: Optional[str] = Field(default=None)
    is_stale: bool = Field(default=False)
    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
