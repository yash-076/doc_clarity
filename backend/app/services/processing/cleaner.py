import re
import unicodedata
from typing import List
from app.schemas.processing import ExtractedContent

class TextCleaner:
    """Safe text normalization service for extracted document elements."""

    def clean_text(self, text: str) -> str:
        if not text:
            return ""

        # 1. Unicode Normalization (NFKC)
        normalized = unicodedata.normalize("NFKC", text)

        # 2. Remove control characters (except newline \n and tab \t)
        cleaned = re.sub(r"[\r\f\v\b\x00-\x08\x0b\x0e-\x1f\x7f]", "", normalized)
        cleaned = cleaned.replace("\ufeff", "")

        # 3. Fix broken line wraps (join words separated by hyphen at line breaks e.g. "com-\npliance" -> "compliance")
        cleaned = re.sub(r"(\w+)-\n(\w+)", r"\1\2", cleaned)
        
        # 4. Collapse multiple spaces into single space per line
        cleaned = re.sub(r"[ \t]+", " ", cleaned)

        # 5. Remove excessive blank lines (more than 2 consecutive newlines)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

        return cleaned.strip()

    def clean_elements(self, elements: List[ExtractedContent]) -> List[ExtractedContent]:
        cleaned_elements: List[ExtractedContent] = []
        for elem in elements:
            cleaned_str = self.clean_text(elem.text)
            if cleaned_str:
                cleaned_elements.append(
                    ExtractedContent(
                        page_number=elem.page_number,
                        text=cleaned_str,
                        section=elem.section,
                        content_type=elem.content_type,
                        extraction_method=elem.extraction_method
                    )
                )
        return cleaned_elements
