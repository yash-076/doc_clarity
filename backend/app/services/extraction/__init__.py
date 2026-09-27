from app.services.extraction.base import DocumentExtractor
from app.services.extraction.pdf_extractor import PDFExtractor
from app.services.extraction.docx_extractor import DOCXExtractor
from app.services.extraction.txt_extractor import TXTExtractor

def get_extractor_for_file(file_path: str) -> DocumentExtractor:
    lower_path = file_path.lower()
    if lower_path.endswith(".pdf"):
        return PDFExtractor()
    elif lower_path.endswith(".docx"):
        return DOCXExtractor()
    elif lower_path.endswith(".txt"):
        return TXTExtractor()
    else:
        raise ValueError(f"Unsupported file format for extraction: {file_path}")

__all__ = [
    "DocumentExtractor",
    "PDFExtractor",
    "DOCXExtractor",
    "TXTExtractor",
    "get_extractor_for_file"
]
