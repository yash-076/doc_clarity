from typing import List
import docx
from app.core.logging import logger
from app.schemas.processing import ExtractedContent
from app.services.extraction.base import DocumentExtractor

class DOCXExtractor(DocumentExtractor):
    """DOCX Extractor supporting paragraph, heading, and table extraction via python-docx."""

    def extract(self, file_path: str) -> List[ExtractedContent]:
        extracted_elements: List[ExtractedContent] = []
        
        try:
            doc = docx.Document(file_path)
        except Exception as e:
            logger.error(f"Failed to open DOCX file {file_path}: {str(e)}")
            raise ValueError(f"Corrupted or invalid DOCX file: {str(e)}")

        current_section = None

        # Process document elements in order
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name.lower() if p.style else ""

            if "heading" in style_name or style_name.startswith("h1") or style_name.startswith("h2"):
                current_section = text
                extracted_elements.append(
                    ExtractedContent(
                        page_number=None,
                        text=text,
                        section=current_section,
                        content_type="heading",
                        extraction_method="text"
                    )
                )
            else:
                extracted_elements.append(
                    ExtractedContent(
                        page_number=None,
                        text=text,
                        section=current_section,
                        content_type="paragraph",
                        extraction_method="text"
                    )
                )

        # Extract table text where present
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    table_rows.append(" | ".join(row_cells))
            
            if table_rows:
                table_text = "\n".join(table_rows)
                extracted_elements.append(
                    ExtractedContent(
                        page_number=None,
                        text=table_text,
                        section=current_section,
                        content_type="table",
                        extraction_method="text"
                    )
                )

        logger.info(f"DOCX extraction completed for {file_path}. Elements count: {len(extracted_elements)}")
        return extracted_elements
