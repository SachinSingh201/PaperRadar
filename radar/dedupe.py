"""Deduplication logic using exact identifiers, canonical URLs, and fuzzy title matching."""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from rapidfuzz import fuzz

from radar.normalize import RadarItem, extract_arxiv_id, normalize_url

logger = logging.getLogger("radar.dedupe")


def clean_title_for_fuzzy(title: str) -> str:
    """Prepares title for fuzzy matching by removing punctuation and lowercasing."""
    if not title:
        return ""
    # Lowercase and strip bracketed tags like [R], [D], [Paper]
    cleaned = re.sub(r"\[.*?\]", "", title.lower())
    # Remove special punctuation
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


class Deduplicator:
    """Deduplicates items using UIDs, normalized URLs, arXiv IDs, and fuzzy title matching."""

    def __init__(self, fuzzy_threshold: float = 90.0):
        self.fuzzy_threshold = fuzzy_threshold
        self.seen_uids: Set[str] = set()
        self.seen_urls: Set[str] = set()
        self.seen_arxiv_ids: Set[str] = set()
        self.seen_titles: List[Tuple[str, str]] = []  # list of (clean_title, uid)

    def register_existing(self, items: List[RadarItem]) -> None:
        """Loads existing items from the database into the deduplication index."""
        for item in items:
            self._register_item(item)

    def _register_item(self, item: RadarItem) -> None:
        if item.uid:
            self.seen_uids.add(item.uid)

        norm_url = normalize_url(item.url)
        if norm_url:
            self.seen_urls.add(norm_url)

        arxiv_id = extract_arxiv_id(item.url) or extract_arxiv_id(item.abstract)
        if arxiv_id:
            self.seen_arxiv_ids.add(arxiv_id)

        clean_t = clean_title_for_fuzzy(item.title)
        if len(clean_t) > 10:
            self.seen_titles.append((clean_t, item.uid))

    def is_duplicate(self, item: RadarItem) -> Tuple[bool, Optional[str]]:
        """Checks if an item is a duplicate.

        Returns:
            Tuple of (is_duplicate: bool, matching_uid_or_reason: str or None)
        """
        # 1. Exact UID match
        if item.uid in self.seen_uids:
            return True, f"exact_uid:{item.uid}"

        # 2. Exact normalized URL match
        norm_url = normalize_url(item.url)
        if norm_url in self.seen_urls:
            return True, f"exact_url:{norm_url}"

        # 3. arXiv ID match
        arxiv_id = extract_arxiv_id(item.url) or extract_arxiv_id(item.abstract)
        if arxiv_id and arxiv_id in self.seen_arxiv_ids:
            return True, f"arxiv_id:{arxiv_id}"

        # 4. Fuzzy title match
        clean_t = clean_title_for_fuzzy(item.title)
        if len(clean_t) > 12:
            for existing_title, existing_uid in self.seen_titles:
                similarity = fuzz.token_set_ratio(clean_t, existing_title)
                if similarity >= self.fuzzy_threshold:
                    return True, f"fuzzy_title:{existing_uid} (ratio {similarity:.1f})"

        return False, None

    def filter_batch(self, items: List[RadarItem]) -> List[RadarItem]:
        """Filters a list of candidate items, discarding duplicates and registering new ones."""
        unique_items: List[RadarItem] = []
        for item in items:
            dup, reason = self.is_duplicate(item)
            if dup:
                logger.debug(f"Discarding duplicate item '{item.title[:40]}...': {reason}")
                continue
            self._register_item(item)
            unique_items.append(item)
        return unique_items
