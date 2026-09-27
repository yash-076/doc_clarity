from app.schemas.processing import ExtractedContent
from app.services.processing.cleaner import TextCleaner
from app.services.processing.structure import StructureDetector
from app.services.processing.chunker import DocumentChunker

def test_text_cleaner():
    cleaner = TextCleaner()
    raw = "  The policy  \n\n\n  provides com-\npliance  for eligible  hospital expenses.  "
    cleaned = cleaner.clean_text(raw)
    assert "com- compliance" not in cleaned
    assert "The policy" in cleaned
    assert "compliance for eligible hospital expenses." in cleaned

def test_structure_detector():
    detector = StructureDetector()
    elements = [
        ExtractedContent(page_number=1, text="SECTION 1: COVERAGE", section=None, content_type="paragraph", extraction_method="text"),
        ExtractedContent(page_number=1, text="This section details eligible claims.", section=None, content_type="paragraph", extraction_method="text"),
    ]
    structured = detector.detect_structure(elements)
    assert structured[0].content_type == "heading"
    assert structured[0].section == "SECTION 1: COVERAGE"
    assert structured[1].section == "SECTION 1: COVERAGE"

def test_document_chunker():
    chunker = DocumentChunker(target_tokens=50, overlap_tokens=10)
    elements = [
        ExtractedContent(page_number=1, text="Headline Section", section="Headline Section", content_type="heading", extraction_method="text"),
        ExtractedContent(page_number=1, text="This is sentence one. " * 15, section="Headline Section", content_type="paragraph", extraction_method="text"),
    ]
    chunks = chunker.create_chunks(elements, document_id="doc_123", document_type="legal")
    assert len(chunks) >= 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["document_type"] == "legal"
    assert "metadata_payload" in chunks[0]
