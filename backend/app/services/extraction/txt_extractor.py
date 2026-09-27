from typing import List
from app.core.logging import logger
from app.schemas.processing import ExtractedContent
from app.services.extraction.base import DocumentExtractor

class TXTExtractor(DocumentExtractor):
    """TXT Extractor reading plain text files with UTF-8 / latin-1 fallback."""

    def extract(self, file_path: str) -> List[ExtractedContent]:
        text_content = ""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    text_content = f.read()
            except Exception as e:
                logger.error(f"Failed to read TXT file with fallback encoding: {str(e)}")
                raise ValueError(f"Could not decode text file: {str(e)}")

        paragraphs = [p.strip() for p in text_content.split("\n\n") if p.strip()]
        if not paragraphs and text_content.strip():
            paragraphs = [text_content.strip()]

        extracted_elements: List[ExtractedContent] = []
        for p in paragraphs:
            extracted_elements.append(
                ExtractedContent(
                    page_number=None,
                    text=p,
                    section=None,
                    content_type="paragraph",
                    extraction_method="text"
                )
            )

        logger.info(f"TXT extraction completed for {file_path}. Elements count: {len(extracted_elements)}")
        return extracted_elements
