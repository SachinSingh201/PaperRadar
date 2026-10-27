"""arXiv API fetcher parsing Atom XML feeds into normalized RadarItems."""

from __future__ import annotations

import datetime
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from radar.fetchers.base import BaseFetcher
from radar.normalize import (
    RadarItem,
    extract_arxiv_id,
    generate_uid,
    parse_iso_date,
    strip_html_tags,
)

logger = logging.getLogger("radar.fetchers.arxiv")

# XML Namespaces for arXiv Atom feed
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def parse_arxiv_xml(xml_content: str, source_id: str = "arxiv-cs-ai") -> List[RadarItem]:
    """Parses arXiv API Atom XML string into a list of RadarItem objects."""
    items: List[RadarItem] = []
    if not xml_content.strip():
        return items

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        logger.error(f"Failed to parse arXiv XML: {e}")
        return items

    entries = root.findall("atom:entry", ATOM_NS)
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for entry in entries:
        id_elem = entry.find("atom:id", ATOM_NS)
        title_elem = entry.find("atom:title", ATOM_NS)
        summary_elem = entry.find("atom:summary", ATOM_NS)
        published_elem = entry.find("atom:published", ATOM_NS)

        if id_elem is None or title_elem is None:
            continue

        url = id_elem.text.strip() if id_elem.text else ""
        raw_title = title_elem.text.strip() if title_elem.text else ""
        title = strip_html_tags(re.sub(r"\s+", " ", raw_title))

        raw_abstract = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ""
        abstract = strip_html_tags(re.sub(r"\s+", " ", raw_abstract))

        # Extract authors
        author_names = []
        for author in entry.findall("atom:author", ATOM_NS):
            name_elem = author.find("atom:name", ATOM_NS)
            if name_elem is not None and name_elem.text:
                author_names.append(name_elem.text.strip())
        authors = ", ".join(author_names)

        # Published date
        published_at = parse_iso_date(published_elem.text.strip()) if published_elem is not None and published_elem.text else now_iso

        arxiv_id = extract_arxiv_id(url)
        uid = generate_uid(url=url, title=title, arxiv_id=arxiv_id)

        # Extract primary category
        primary_cat_elem = entry.find("arxiv:primary_category", ATOM_NS)
        category = primary_cat_elem.get("term") if primary_cat_elem is not None else "cs.AI"

        item = RadarItem(
            uid=uid,
            title=title,
            authors=authors,
            org="arXiv",
            source=source_id,
            source_type="paper",
            url=url,
            published_at=published_at,
            fetched_at=now_iso,
            abstract=abstract,
            extra_metadata={"arxiv_category": category},
        )
        items.append(item)

    return items


class ArxivFetcher(BaseFetcher):
    """Fetcher for the official arXiv query API."""

    def fetch(self, source_info: Dict[str, Any]) -> List[RadarItem]:
        url = source_info.get("url")
        source_id = source_info.get("id", "arxiv")
        if not url:
            return []

        logger.info(f"Fetching arXiv feed: {url}")
        resp, reason = self.http_client.get(url, is_api=True)
        if resp is None:
            logger.warning(f"Failed to fetch arXiv feed: {reason}")
            return []

        return parse_arxiv_xml(resp.text, source_id=source_id)
