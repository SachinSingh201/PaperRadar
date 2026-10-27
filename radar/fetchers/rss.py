"""Generic RSS and Atom feed fetcher using polite HTTP client and feedparser."""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, List, Optional
import feedparser
from radar.fetchers.base import BaseFetcher
from radar.normalize import (
    RadarItem,
    generate_uid,
    parse_iso_date,
    strip_html_tags,
)

logger = logging.getLogger("radar.fetchers.rss")


def parse_rss_content(content: str, source_info: Dict[str, Any]) -> List[RadarItem]:
    """Parses raw RSS or Atom XML content into normalized RadarItems."""
    feed = feedparser.parse(content)
    items: List[RadarItem] = []
    source_id = source_info.get("id", "rss")
    source_type = source_info.get("type", "blog")
    org_name = source_info.get("org", "")
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for entry in feed.entries:
        title = strip_html_tags(getattr(entry, "title", ""))
        link = getattr(entry, "link", "")
        if not title or not link:
            continue

        # Extract abstract/summary
        raw_summary = ""
        if hasattr(entry, "summary"):
            raw_summary = entry.summary
        elif hasattr(entry, "description"):
            raw_summary = entry.description
        elif hasattr(entry, "content") and entry.content:
            raw_summary = entry.content[0].value

        abstract = strip_html_tags(raw_summary)

        # Extract authors
        author = getattr(entry, "author", "")
        if not author and hasattr(entry, "authors"):
            author = ", ".join(a.get("name", "") for a in entry.authors if "name" in a)

        # Date handling
        raw_date = None
        for date_attr in ("published", "pubDate", "updated", "created"):
            if hasattr(entry, date_attr):
                raw_date = getattr(entry, date_attr)
                break
        published_at = parse_iso_date(raw_date)

        uid = generate_uid(url=link, title=title)

        item = RadarItem(
            uid=uid,
            title=title,
            authors=author,
            org=org_name,
            source=source_id,
            source_type=source_type,
            url=link,
            published_at=published_at,
            fetched_at=now_iso,
            abstract=abstract,
        )
        items.append(item)

    return items


class RssFetcher(BaseFetcher):
    """Fetcher for RSS and Atom web feeds."""

    def fetch(self, source_info: Dict[str, Any]) -> List[RadarItem]:
        url = source_info.get("url")
        if not url:
            return []

        logger.info(f"Fetching RSS feed: {url}")
        resp, reason = self.http_client.get(url)
        if resp is None:
            logger.warning(f"Failed to fetch RSS feed {url}: {reason}")
            return []

        if reason == "not_modified":
            logger.info(f"Feed unchanged (304): {url}")
            return []

        return parse_rss_content(resp.text, source_info)
