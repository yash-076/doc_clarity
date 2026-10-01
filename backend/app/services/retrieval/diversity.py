import logging
import re
from typing import List

from app.core.config import settings
from app.services.retrieval.models import RetrievedCandidate

logger = logging.getLogger(__name__)


def apply_section_and_page_boosting(query: str, candidates: List[RetrievedCandidate]) -> List[RetrievedCandidate]:
    """Detects explicit section or page references in query and boosts candidate scores."""
    if not candidates:
        return candidates

    query_lower = query.lower()

    # Detect page number pattern e.g., "page 12", "p. 12"
    page_match = re.search(r'\b(?:page|p\.)\s*(\d+)\b', query_lower)
    target_page = int(page_match.group(1)) if page_match else None

    # Detect section pattern e.g., "section 8", "sec 8.2", "clause 4"
    sec_match = re.search(r'\b(?:section|sec|clause)\s*([0-9\.\w]+)\b', query_lower)
    target_section = sec_match.group(1).lower() if sec_match else None

    for c in candidates:
        boost = 1.0
        if target_page is not None and c.page_number == target_page:
            boost += 0.5
            logger.info(f"Page boost applied to chunk {c.chunk_id} (page {c.page_number})")

        if target_section is not None and c.section:
            sec_str = str(c.section).lower()
            if target_section in sec_str:
                boost += 0.5
                logger.info(f"Section boost applied to chunk {c.chunk_id} (section '{c.section}')")

        c.final_score *= boost

    candidates.sort(key=lambda x: x.final_score, reverse=True)
    return candidates


def apply_diversity_selection(candidates: List[RetrievedCandidate], top_k: int = 5, max_per_section: int = 2) -> List[RetrievedCandidate]:
    """Selects top_k candidates ensuring context diversity across sections and pages."""
    if not candidates or not settings.DIVERSITY_SELECTION_ENABLED or len(candidates) <= top_k:
        return candidates[:top_k]

    selected: List[RetrievedCandidate] = []
    section_counts: dict[str, int] = {}
    page_counts: dict[int, int] = {}

    # First pass: Pick high scoring items respecting section/page limits
    remaining: List[RetrievedCandidate] = []
    for c in candidates:
        sec_key = (c.section or "unknown").strip().lower()
        page_key = c.page_number if c.page_number is not None else -1

        sec_count = section_counts.get(sec_key, 0)
        page_count = page_counts.get(page_key, 0)

        if len(selected) < top_k and sec_count < max_per_section and page_count < max_per_section:
            selected.append(c)
            section_counts[sec_key] = sec_count + 1
            if page_key != -1:
                page_counts[page_key] = page_count + 1
        else:
            remaining.append(c)

    # Second pass: Fill remaining slots if needed
    while len(selected) < top_k and remaining:
        selected.append(remaining.pop(0))

    return selected
