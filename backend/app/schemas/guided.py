import uuid
from typing import Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.core.personas import PersonaType
from app.schemas.rag import CitationItem


class SuggestedQuestionsRequest(BaseModel):
    """Schema for requesting document-specific suggested questions."""
    persona: Optional[PersonaType] = Field(
        default=PersonaType.CONSUMER,
        description="Optional persona context for suggested questions generation."
    )
    force_refresh: bool = Field(
        default=False,
        description="If true, forces re-generation of suggested questions from analysis."
    )


class SuggestedQuestionItem(BaseModel):
    """Item schema for a suggested question."""
    id: str = Field(..., description="Unique question identifier (e.g. q1, q2).")
    question: str = Field(..., description="Concise, document-grounded question string.")
    category: str = Field(..., description="Controlled category tag (e.g., coverage, exclusions, deadlines, financial).")

    model_config = ConfigDict(from_attributes=True)


class SuggestedQuestionsResponse(BaseModel):
    """Structured response containing suggested questions for a document."""
    document_id: uuid.UUID = Field(..., description="Target document ID.")
    persona: PersonaType = Field(default=PersonaType.CONSUMER, description="Persona style used for suggested questions.")
    analysis_version: int = Field(default=1, description="Phase 5 analysis version used to generate questions.")
    questions: List[SuggestedQuestionItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CreateConversationRequest(BaseModel):
    """Schema for starting a new multi-turn conversation session."""
    title: Optional[str] = Field(default=None, description="Optional custom conversation title.")
    persona: Optional[PersonaType] = Field(
        default=PersonaType.CONSUMER,
        description="Initial explanation persona style (consumer, professional, business)."
    )


class SendMessageRequest(BaseModel):
    """Schema for sending a user message in a conversation session."""
    content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User question or follow-up query text."
    )
    persona: Optional[PersonaType] = Field(
        default=None,
        description="Optional persona override for this message/conversation session."
    )

    @field_validator("content")
    @classmethod
    def validate_content_non_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty or whitespace only.")
        return stripped


class MessageResponse(BaseModel):
    """Schema for a single message in a conversation trajectory."""
    id: uuid.UUID = Field(..., description="Unique message UUID.")
    conversation_id: uuid.UUID = Field(..., description="Parent conversation UUID.")
    role: Literal["user", "assistant"] = Field(..., description="Message sender role.")
    content: str = Field(..., description="Message text content.")
    persona: Optional[PersonaType] = Field(default=PersonaType.CONSUMER, description="Persona style used for this response.")
    citations: List[CitationItem] = Field(default_factory=list, description="Source citations if role is assistant.")
    confidence: Optional[str] = Field(default=None, description="Confidence indicator if role is assistant.")
    created_at: Optional[str] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    """Schema for complete conversation state and history."""
    id: uuid.UUID = Field(..., description="Unique conversation UUID.")
    document_id: uuid.UUID = Field(..., description="Target document UUID.")
    title: Optional[str] = Field(default=None)
    persona: PersonaType = Field(default=PersonaType.CONSUMER, description="Active conversation persona style.")
    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)
    messages: List[MessageResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
