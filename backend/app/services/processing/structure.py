import re
from typing import List
from app.schemas.processing import ExtractedContent

HEADING_PATTERNS = [
    r"^(ARTICLE|SECTION|CHAPTER|PART|CLAUSE)\s+[\dA-Z]+.*$",
    r"^\d+(\.\d+)*\s+[A-Z].*$",
    r"^(COVERAGE|EXCLUSIONS|LIMITATIONS|DEFINITIONS|TERMINATION|ELIGIBILITY|SCHEDULE|CONDITIONS|BENEFITS)$",
]

class StructureDetector:
    """Deterministic structure detector to infer sections and headings."""

    def is_heading(self, text: str, content_type: str) -> bool:
        if content_type in ["heading", "title"]:
            return True

        text_upper = text.strip().upper()
        
        # Check against regex heading patterns
        for pattern in HEADING_PATTERNS:
            if re.match(pattern, text_upper):
                return True

        # Check for short all-caps lines (3 to 60 characters)
        if len(text) <= 60 and text.isupper() and not text.endswith("."):
            return True

        return False

    def detect_structure(self, elements: List[ExtractedContent]) -> List[ExtractedContent]:
        structured_elements: List[ExtractedContent] = []
        current_section: str | None = None

        for elem in elements:
            text = elem.text.strip()
            
            if self.is_heading(text, elem.content_type):
                current_section = text
                structured_elements.append(
                    ExtractedContent(
                        page_number=elem.page_number,
                        text=text,
                        section=current_section,
                        content_type="heading",
                        extraction_method=elem.extraction_method
                    )
                )
            else:
                # Assign section if element didn't have one
                section_name = elem.section or current_section
                content_type = elem.content_type
                if text.startswith(("- ", "* ", "• ", "1. ", "a. ")):
                    content_type = "list"

                structured_elements.append(
                    ExtractedContent(
                        page_number=elem.page_number,
                        text=text,
                        section=section_name,
                        content_type=content_type,
                        extraction_method=elem.extraction_method
                    )
                )

        return structured_elements
