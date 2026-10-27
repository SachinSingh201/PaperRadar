"""Hugging Face Daily Papers API fetcher."""

from __future__ import annotations

import datetime
import json
import logging
from typing import Any, Dict, List, Optional
from radar.fetchers.base import BaseFetcher
from radar.normalize import (
    RadarItem,
    generate_uid,
    parse_iso_date,
    strip_html_tags,
)

logger = logging.getLogger("radar.fetchers.huggingface")


def parse_hf_papers_json(data: Any, source_info: Dict[str, Any]) -> List[RadarItem]:
    """Parses Hugging Face Daily Papers API JSON payload into normalized RadarItems."""
    items: List[RadarItem] = []
    if not isinstance(data, list):
        if isinstance(data, dict) and "papers" in data:
            data = data["papers"]
        else:
            return items

    source_id = source_info.get("id", "huggingface-daily-papers")
    org_name = source_info.get("org", "Hugging Face")
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for entry in data:
        paper = entry.get("paper", entry) if isinstance(entry, dict) else {}
        paper_id = paper.get("id") or entry.get("id")
        title = strip_html_tags(paper.get("title") or "")
        summary = strip_html_tags(paper.get("summary") or "")

        if not paper_id or not title:
            continue

        raw_authors = paper.get("authors") or []
        authors_list = []
        if isinstance(raw_authors, list):
            for a in raw_authors:
                if isinstance(a, dict) and "name" in a:
                    authors_list.append(a["name"])
                elif isinstance(a, str):
                    authors_list.append(a)
        authors = ", ".join(authors_list)

        upvotes = paper.get("upvotes", entry.get("upvotes", 0))
        published_raw = paper.get("publishedAt") or entry.get("publishedAt")
        published_at = parse_iso_date(published_raw)

        url = f"https://huggingface.co/papers/{paper_id}"
        uid = f"arxiv:{paper_id}"

        item = RadarItem(
            uid=uid,
            title=title,
            authors=authors,
            org=org_name,
            source=source_id,
            source_type="paper",
            url=url,
            published_at=published_at,
            fetched_at=now_iso,
            abstract=summary,
            extra_metadata={"upvotes": int(upvotes) if upvotes else 0, "hf_paper_id": paper_id},
        )
        items.append(item)

    return items


class HuggingFaceFetcher(BaseFetcher):
    """Fetcher for the official Hugging Face Daily Papers API."""

    def fetch(self, source_info: Dict[str, Any]) -> List[RadarItem]:
        url = source_info.get("url", "https://huggingface.co/api/daily_papers")
        logger.info(f"Fetching Hugging Face daily papers: {url}")

        resp, reason = self.http_client.get(url, is_api=True)
        if resp is None:
            logger.warning(f"Failed to fetch Hugging Face papers: {reason}")
            return []

        try:
            data = resp.json()
            return parse_hf_papers_json(data, source_info)
        except Exception as e:
            logger.error(f"Failed to parse Hugging Face JSON: {e}")
            return []
