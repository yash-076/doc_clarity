import io
import pymupdf as fitz  # PyMuPDF
import pytesseract
from PIL import Image
from typing import List

from app.core.config import settings
from app.core.logging import logger
from app.schemas.processing import ExtractedContent
from app.services.extraction.base import DocumentExtractor

class PDFExtractor(DocumentExtractor):
    """PDF Extractor supporting PyMuPDF native extraction with automatic Tesseract OCR fallback."""

    def __init__(self):
        if settings.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    def extract(self, file_path: str) -> List[ExtractedContent]:
        extracted_elements: List[ExtractedContent] = []
        
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.error(f"Failed to open PDF file {file_path}: {str(e)}")
            raise ValueError(f"Corrupted or invalid PDF file: {str(e)}")

        native_pages_count = 0
        ocr_pages_count = 0

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc.load_page(page_idx)
            
            # 1. Attempt native text extraction
            native_text = page.get_text("text").strip()
            meaningful_chars = len([c for c in native_text if c.isalnum()])

            if meaningful_chars >= settings.OCR_MIN_TEXT_CHARS:
                native_pages_count += 1
                extracted_elements.append(
                    ExtractedContent(
                        page_number=page_num,
                        text=native_text,
                        section=None,
                        content_type="page_content",
                        extraction_method="text"
                    )
                )
            else:
                # 2. Trigger Tesseract OCR Fallback
                if not settings.OCR_ENABLED:
                    logger.warning(f"Page {page_num} has insufficient text ({meaningful_chars} chars), but OCR is disabled.")
                    if native_text:
                        extracted_elements.append(
                            ExtractedContent(
                                page_number=page_num,
                                text=native_text,
                                section=None,
                                content_type="page_content",
                                extraction_method="text"
                            )
                        )
                    continue

                logger.info(f"Page {page_num} has insufficient text ({meaningful_chars} chars). Running Tesseract OCR fallback...")
                try:
                    # Render PDF page to high-DPI image
                    pix = page.get_pixmap(dpi=settings.OCR_DPI)
                    img_bytes = pix.tobytes("png")
                    image = Image.open(io.BytesIO(img_bytes))

                    # Perform OCR
                    ocr_text = pytesseract.image_to_string(
                        image,
                        lang=settings.OCR_LANGUAGE
                    ).strip()

                    ocr_pages_count += 1
                    extracted_elements.append(
                        ExtractedContent(
                            page_number=page_num,
                            text=ocr_text if ocr_text else native_text,
                            section=None,
                            content_type="page_content",
                            extraction_method="ocr" if ocr_text else "text"
                        )
                    )
                except pytesseract.TesseractNotFoundError:
                    err_msg = "OCR is required for this document, but Tesseract OCR is not installed or configured correctly."
                    logger.error(err_msg)
                    raise RuntimeError(err_msg)
                except Exception as ocr_err:
                    err_msg = f"Tesseract OCR failed on page {page_num}: {str(ocr_err)}"
                    logger.error(err_msg)
                    raise RuntimeError(err_msg)

        doc.close()
        logger.info(f"PDF extraction completed for {file_path}. Native pages: {native_pages_count}, OCR pages: {ocr_pages_count}")
        return extracted_elements
