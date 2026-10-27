"""GitHub Releases Atom feed fetcher for tracking open-source models, engines, and protocols."""

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

logger = logging.getLogger("radar.fetchers.github_releases")


def parse_github_atom(content: str, source_info: Dict[str, Any]) -> List[RadarItem]:
    """Parses GitHub Releases Atom feed XML into normalized RadarItems."""
    feed = feedparser.parse(content)
    items: List[RadarItem] = []
    source_id = source_info.get("id", "github-release")
    source_type = source_info.get("type", "release")
    org_name = source_info.get("org", "Open Source")
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for entry in feed.entries:
        title = strip_html_tags(getattr(entry, "title", ""))
        link = getattr(entry, "link", "")
        if not title or not link:
            continue

        raw_content = ""
        if hasattr(entry, "content") and entry.content:
            raw_content = entry.content[0].value
        elif hasattr(entry, "summary"):
            raw_content = entry.summary

        abstract = strip_html_tags(raw_content)
        # Keep abstract reasonably concise
        if len(abstract) > 600:
            abstract = abstract[:597] + "..."

        author = getattr(entry, "author", org_name)
        published_raw = getattr(entry, "updated", getattr(entry, "published", None))
        published_at = parse_iso_date(published_raw)

        uid = generate_uid(url=link, title=title)

        item = RadarItem(
            uid=uid,
            title=f"{source_info.get('name', 'Release')}: {title}",
            authors=author,
            org=org_name,
            source=source_id,
            source_type=source_type,
            url=link,
            published_at=published_at,
            fetched_at=now_iso,
            abstract=abstract,
            extra_metadata={"release_title": title},
        )
        items.append(item)

    return items


class GithubReleasesFetcher(BaseFetcher):
    """Fetcher for GitHub Releases Atom feeds."""

    def fetch(self, source_info: Dict[str, Any]) -> List[RadarItem]:
        url = source_info.get("url")
        if not url:
            return []

        logger.info(f"Fetching GitHub releases feed: {url}")
        resp, reason = self.http_client.get(url)
        if resp is None:
            logger.warning(f"Failed to fetch GitHub feed {url}: {reason}")
            return []

        if reason == "not_modified":
            return []

        return parse_github_atom(resp.text, source_info)
