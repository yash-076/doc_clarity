from enum import Enum
from typing import Dict, Any


class PersonaType(str, Enum):
    CONSUMER = "consumer"
    PROFESSIONAL = "professional"
    BUSINESS = "business"


PERSONA_CONFIG: Dict[str, Dict[str, Any]] = {
    PersonaType.CONSUMER.value: {
        "name": "Consumer",
        "description": "Simple explanations with minimal jargon.",
        "tagline": "Clear, plain English explanation",
        "instructions": (
            "Explain the document in clear, simple language suitable for a layperson.\n"
            "Avoid unnecessary technical or legal jargon. When a technical term is necessary, explain it briefly in plain English.\n"
            "Use short, accessible paragraphs and focus on practical implications ('what this means for you').\n"
            "Do NOT remove important conditions, exceptions, dates, amounts, or limitations merely to make the answer simpler."
        ),
        "question_prefix": "What does this mean for me regarding",
    },
    PersonaType.PROFESSIONAL.value: {
        "name": "Professional",
        "description": "Technical explanations with precise terms and clause references.",
        "tagline": "Rigorous technical & legal precision",
        "instructions": (
            "Use precise technical, legal, insurance, or medical terminology as present in the document.\n"
            "Preserve exact clause structure, section titles, page references, and qualifying conditions.\n"
            "Clearly distinguish explicit document language from interpretation.\n"
            "Preserve all exceptions, conditions, qualifications, and limitations in full detail without oversimplifying."
        ),
        "question_prefix": "Which explicit clauses or sections govern",
    },
    PersonaType.BUSINESS.value: {
        "name": "Business",
        "description": "Focus on costs, obligations, deadlines, liabilities, and operational impact.",
        "tagline": "Operational, financial, and risk focus",
        "instructions": (
            "Focus on operationally relevant business information such as obligations, deadlines, monetary costs, "
            "financial terms, liability, termination provisions, renewal criteria, and operational restrictions.\n"
            "Explain practical business implications strictly when supported by the document evidence.\n"
            "Highlight actionable items, important dates, and potential operational risks clearly."
        ),
        "question_prefix": "What financial, operational, or deadline obligations apply to",
    },
}


def ensure_persona(persona: Any) -> PersonaType:
    """Safely coerces string or PersonaType input to a valid PersonaType enum, defaulting to CONSUMER."""
    if isinstance(persona, PersonaType):
        return persona
    if isinstance(persona, str):
        val = persona.lower().strip()
        if val in PersonaType._value2member_map_:
            return PersonaType(val)
    return PersonaType.CONSUMER


def get_persona_instructions(persona: Any) -> str:
    """Returns system prompt instruction snippet for a given persona."""
    p_enum = ensure_persona(persona)
    config = PERSONA_CONFIG.get(p_enum.value, PERSONA_CONFIG[PersonaType.CONSUMER.value])
    return config["instructions"]
