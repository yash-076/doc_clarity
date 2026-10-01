import io
import pymupdf as fitz
import docx
from app.services.extraction.pdf_extractor import PDFExtractor
from app.services.extraction.docx_extractor import DOCXExtractor
from app.services.extraction.txt_extractor import TXTExtractor

def test_pdf_extractor_native(tmp_path):
    pdf_path = tmp_path / "test_native.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "This is a native text PDF page for testing PyMuPDF extraction in Doc Clarity.")
    doc.save(str(pdf_path))
    doc.close()

    extractor = PDFExtractor()
    elements = extractor.extract(str(pdf_path))
    assert len(elements) == 1
    assert elements[0].page_number == 1
    assert elements[0].extraction_method == "text"
    assert "native text PDF page" in elements[0].text

def test_docx_extractor(tmp_path):
    docx_path = tmp_path / "test.docx"
    doc = docx.Document()
    doc.add_heading("Coverage Details", level=1)
    doc.add_paragraph("This policy covers eligible emergency medical treatment.")
    doc.save(str(docx_path))

    extractor = DOCXExtractor()
    elements = extractor.extract(str(docx_path))
    assert len(elements) == 2
    assert elements[0].content_type == "heading"
    assert elements[0].section == "Coverage Details"
    assert elements[1].content_type == "paragraph"

def test_txt_extractor(tmp_path):
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("Header Section\n\nParagraph 1 describing terms.\n\nParagraph 2 describing exclusions.", encoding="utf-8")

    extractor = TXTExtractor()
    elements = extractor.extract(str(txt_path))
    assert len(elements) == 3
    assert elements[0].extraction_method == "text"
