import re
from typing import List, Dict, Any
from app.core.config import settings
from app.schemas.processing import ExtractedContent

class DocumentChunker:
    """Structure-aware semantic chunker with configurable size and overlap."""

    def __init__(self, target_tokens: int | None = None, overlap_tokens: int | None = None):
        self.target_tokens = target_tokens or settings.CHUNK_SIZE
        self.overlap_tokens = overlap_tokens or settings.CHUNK_OVERLAP
        
        # Character approximation (~4 characters per token)
        self.max_chars = self.target_tokens * 4
        self.overlap_chars = self.overlap_tokens * 4

    def _split_long_text(self, text: str) -> List[str]:
        """Split oversized text into overlapping chunks along sentence boundaries."""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sub_chunks: List[str] = []
        current_str = ""

        for sentence in sentences:
            if len(current_str) + len(sentence) <= self.max_chars:
                current_str += (" " if current_str else "") + sentence
            else:
                if current_str:
                    sub_chunks.append(current_str.strip())
                    # Apply overlap from the end of current_str
                    overlap = current_str[-self.overlap_chars:] if len(current_str) > self.overlap_chars else current_str
                    current_str = overlap + " " + sentence
                else:
                    # Single sentence exceeds max_chars, force split by character
                    sub_chunks.append(sentence[:self.max_chars].strip())
                    current_str = sentence[self.max_chars - self.overlap_chars:]

        if current_str.strip():
            sub_chunks.append(current_str.strip())

        return sub_chunks

    def create_chunks(
        self,
        elements: List[ExtractedContent],
        document_id: str,
        document_type: str
    ) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        current_chunk_text = ""
        current_page: int | None = None
        current_section: str | None = None
        current_methods: set[str] = set()
        chunk_index = 0

        for elem in elements:
            elem_text = elem.text.strip()
            if not elem_text:
                continue

            # Track section and page
            if elem.section:
                current_section = elem.section
            if elem.page_number is not None:
                current_page = elem.page_number
            current_methods.add(elem.extraction_method)

            # Check if adding this element exceeds max_chars
            if len(current_chunk_text) + len(elem_text) + 2 > self.max_chars:
                if current_chunk_text.strip():
                    method = "ocr" if "ocr" in current_methods else "text"
                    chunks.append({
                        "chunk_index": chunk_index,
                        "text": current_chunk_text.strip(),
                        "page_number": current_page,
                        "section": current_section,
                        "document_type": document_type,
                        "extraction_method": method,
                        "metadata_payload": {
                            "document_id": document_id,
                            "chunk_index": chunk_index,
                            "page_number": current_page,
                            "section": current_section,
                            "document_type": document_type,
                            "extraction_method": method
                        }
                    })
                    chunk_index += 1
                    
                    # Prepare overlap text for next chunk
                    overlap = current_chunk_text[-self.overlap_chars:] if len(current_chunk_text) > self.overlap_chars else ""
                    current_chunk_text = overlap + "\n\n" + elem_text
                    current_methods = {elem.extraction_method}
                else:
                    # Single element is oversized, split it
                    sub_pieces = self._split_long_text(elem_text)
                    for piece in sub_pieces:
                        chunks.append({
                            "chunk_index": chunk_index,
                            "text": piece,
                            "page_number": current_page,
                            "section": current_section,
                            "document_type": document_type,
                            "extraction_method": elem.extraction_method,
                            "metadata_payload": {
                                "document_id": document_id,
                                "chunk_index": chunk_index,
                                "page_number": current_page,
                                "section": current_section,
                                "document_type": document_type,
                                "extraction_method": elem.extraction_method
                            }
                        })
                        chunk_index += 1
                    current_chunk_text = ""
                    current_methods = set()
            else:
                if current_chunk_text:
                    current_chunk_text += "\n\n" + elem_text
                else:
                    current_chunk_text = elem_text

        # Add remaining text
        if current_chunk_text.strip():
            method = "ocr" if "ocr" in current_methods else "text"
            chunks.append({
                "chunk_index": chunk_index,
                "text": current_chunk_text.strip(),
                "page_number": current_page,
                "section": current_section,
                "document_type": document_type,
                "extraction_method": method,
                "metadata_payload": {
                    "document_id": document_id,
                    "chunk_index": chunk_index,
                    "page_number": current_page,
                    "section": current_section,
                    "document_type": document_type,
                    "extraction_method": method
                }
            })

        return chunks
