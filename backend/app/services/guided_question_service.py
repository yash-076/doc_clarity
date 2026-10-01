import json
import logging
import uuid
from typing import Optional, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.document import Document, DocumentStatus, EmbeddingStatus
from app.db.models.document_analysis import DocumentAnalysis
from app.db.models.document_question import DocumentQuestion
from app.schemas.guided import (
    SuggestedQuestionsResponse,
    SuggestedQuestionItem,
)
from app.services.analysis_service import DocumentAnalysisService
from app.services.llm import LLMService, get_llm_service

logger = logging.getLogger(__name__)

QUESTION_GEN_SYSTEM_PROMPT = """You are Doc Clarity, a document question-generation assistant.

Your task is to generate useful, document-grounded suggested questions that a user would reasonably want to ask after inspecting the provided document analysis.

Rules:
1. Questions MUST be answerable using the document context.
2. Do NOT use outside knowledge or invent topics not present in the analysis.
3. Avoid generic questions like "What is this document?" or "Can you summarize this?".
4. Prioritize important exclusions, obligations, deadlines, financial terms, restrictions, and high-attention risk items.
5. Avoid duplicate or semantically redundant questions.
6. Keep questions concise, natural, and directly relevant to the document domain type.
7. Return ONLY a single valid JSON object strictly matching: {"questions": [{"id": "q1", "question": "...", "category": "..."}]}"""


class GuidedQuestionService:
    """Service for generating, caching, and retrieving document-specific suggested questions."""

    def __init__(
        self,
        analysis_service: Optional[DocumentAnalysisService] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.analysis_service = analysis_service or DocumentAnalysisService()
        self.llm_service = llm_service or get_llm_service()

    async def get_or_generate_questions(
        self,
        db: Session,
        document_id: uuid.UUID,
        force_refresh: bool = False,
    ) -> SuggestedQuestionsResponse:
        """Retrieves cached suggested questions or generates fresh ones based on Phase 5 analysis."""

        # 1. Validate Document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with ID {document_id} not found."
            )

        if document.status != DocumentStatus.READY.value and document.status != DocumentStatus.READY:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document processing is not complete yet (status: '{document.status}')."
            )

        # 2. Get Phase 5 Analysis (creates if not existing)
        analysis_resp = await self.analysis_service.get_or_create_analysis(
            db=db,
            document_id=document_id,
            force_refresh=False,
        )
        current_analysis_version = analysis_resp.analysis_version

        # 3. Check for cached questions matching current analysis_version
        if not force_refresh:
            cached_questions = (
                db.query(DocumentQuestion)
                .filter(
                    DocumentQuestion.document_id == document_id,
                    DocumentQuestion.analysis_version == current_analysis_version,
                )
                .order_by(DocumentQuestion.position.asc())
                .all()
            )
            if cached_questions and not self._is_generic_fallback(cached_questions):
                logger.info(f"Returning {len(cached_questions)} cached suggested questions for document_id={document_id}")
                return SuggestedQuestionsResponse(
                    document_id=document_id,
                    analysis_version=current_analysis_version,
                    questions=[
                        SuggestedQuestionItem(
                            id=q.question_id_str if hasattr(q, "question_id_str") else f"q{idx+1}",
                            question=q.question,
                            category=q.category,
                        )
                        for idx, q in enumerate(cached_questions)
                    ]
                )

        # 4. Generate Fresh Questions via LLM
        logger.info(f"Generating fresh suggested questions for document_id={document_id}")
        user_prompt = self._build_generation_prompt(document, analysis_resp)

        raw_llm_response = await self.llm_service.generate(
            system_prompt=QUESTION_GEN_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        questions_list = self._parse_and_deduplicate_questions(
            raw_text=raw_llm_response,
            analysis=analysis_resp,
            document=document,
        )

        # 5. Clear old questions for this document and store new ones
        db.query(DocumentQuestion).filter(DocumentQuestion.document_id == document_id).delete()

        db_questions = []
        for idx, item in enumerate(questions_list, start=1):
            q_obj = DocumentQuestion(
                id=uuid.uuid4(),
                document_id=document_id,
                question=item["question"],
                category=item["category"],
                position=idx,
                analysis_version=current_analysis_version,
            )
            db_questions.append(q_obj)

        db.add_all(db_questions)
        db.commit()

        return SuggestedQuestionsResponse(
            document_id=document_id,
            analysis_version=current_analysis_version,
            questions=[
                SuggestedQuestionItem(
                    id=f"q{idx+1}",
                    question=q.question,
                    category=q.category,
                )
                for idx, q in enumerate(db_questions)
            ]
        )

    async def get_cached_questions(self, db: Session, document_id: uuid.UUID) -> SuggestedQuestionsResponse:
        """Retrieves existing cached questions for a document, auto-refreshing if generic fallback was stored."""
        questions = (
            db.query(DocumentQuestion)
            .filter(DocumentQuestion.document_id == document_id)
            .order_by(DocumentQuestion.position.asc())
            .all()
        )
        if not questions or self._is_generic_fallback(questions):
            return await self.get_or_generate_questions(db=db, document_id=document_id, force_refresh=True)

        analysis_version = questions[0].analysis_version if questions else 1
        return SuggestedQuestionsResponse(
            document_id=document_id,
            analysis_version=analysis_version,
            questions=[
                SuggestedQuestionItem(
                    id=f"q{idx+1}",
                    question=q.question,
                    category=q.category,
                )
                for idx, q in enumerate(questions)
            ]
        )

    def _is_generic_fallback(self, questions: list) -> bool:
        """Checks if questions list contains generic fallback templates."""
        generic_phrases = [
            "coverage scope or primary terms",
            "conditions, limitations, or exclusions",
            "important deadlines or dates specified",
            "monetary amounts, fees, or penalties",
            "primary obligations or responsibilities",
            "termination or claim rejection",
        ]
        for q in questions:
            q_text = (getattr(q, "question", str(q)) or "").lower()
            if any(phrase in q_text for phrase in generic_phrases):
                return True
        return False


    def _build_generation_prompt(self, document: Document, analysis: Any) -> str:
        """Constructs context prompt from Phase 5 analysis."""
        summary_text = getattr(analysis, "summary", "") or ""
        key_points = [f"- {kp.title}: {kp.description}" for kp in getattr(analysis, "key_points", [])]
        dates = [f"- {d.description}: {d.date}" for d in getattr(analysis, "important_dates", [])]
        financials = [f"- {f.description}: {f.amount}" for f in getattr(analysis, "financial_terms", [])]
        obligations = [f"- [{o.party}] {o.description}" for o in getattr(analysis, "obligations", [])]
        exclusions = [f"- {e.description}" for e in getattr(analysis, "exclusions", [])]
        attention = [f"- [{att.severity.upper()}] {att.title}: {att.description}" for att in getattr(analysis, "attention_items", [])]

        prompt = f"""DOCUMENT METADATA
Filename: {document.original_filename}
Domain Type: {document.document_type}

EXECUTIVE SUMMARY:
{summary_text}

HIGH-ATTENTION RISK ITEMS:
{chr(10).join(attention) if attention else 'None'}

EXCLUSIONS & LIMITATIONS:
{chr(10).join(exclusions) if exclusions else 'None'}

FINANCIAL TERMS:
{chr(10).join(financials) if financials else 'None'}

OBLIGATIONS:
{chr(10).join(obligations) if obligations else 'None'}

IMPORTANT DATES:
{chr(10).join(dates) if dates else 'None'}

KEY POINTS:
{chr(10).join(key_points) if key_points else 'None'}

INSTRUCTIONS:
Generate exactly {settings.SUGGESTED_QUESTION_COUNT} useful, document-grounded questions targeting specific facts, clauses, exclusions, deadlines, or amounts mentioned above in '{document.original_filename}'.
Include specific terms or clause details from the document in each question.
Return JSON format ONLY: {{"questions": [{{"id": "q1", "question": "...", "category": "..."}}]}}"""
        return prompt

    def _parse_and_deduplicate_questions(
        self,
        raw_text: str,
        analysis: Any = None,
        document: Any = None
    ) -> list[dict[str, str]]:
        """Parses LLM output using robust regex and generates document-specific dynamic questions."""
        cleaned = raw_text.strip()
        parsed_list = []

        # Robust JSON extraction using regex pattern matching
        import re
        json_match = re.search(r'(\{.*"questions".*\})', cleaned, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                raw_qs = data.get("questions", [])
                for item in raw_qs:
                    if isinstance(item, dict) and "question" in item:
                        parsed_list.append({
                            "question": item["question"].strip(),
                            "category": item.get("category", "overview").strip().lower()
                        })
            except Exception as e:
                logger.warning(f"Regex extracted JSON parse failed: {str(e)}")

        if not parsed_list:
            # Fallback simple stripping
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            try:
                data = json.loads(cleaned.strip())
                raw_qs = data.get("questions", [])
                for item in raw_qs:
                    if isinstance(item, dict) and "question" in item:
                        parsed_list.append({
                            "question": item["question"].strip(),
                            "category": item.get("category", "overview").strip().lower()
                        })
            except Exception as e:
                logger.error(f"Failed to parse question generation JSON: {str(e)}")


        # Deduplicate by lowercase question string
        seen = set()
        deduped = []
        for item in parsed_list:
            q_norm = item["question"].lower()
            if q_norm not in seen:
                seen.add(q_norm)
                deduped.append(item)

        return deduped[:settings.MAX_SUGGESTED_QUESTIONS]

