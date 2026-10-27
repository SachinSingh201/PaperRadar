"""Data normalization and item schema definitions for Paper Radar."""

from __future__ import annotations

import datetime
import hashlib
import html
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from bs4 import BeautifulSoup
from dateutil import parser as date_parser


@dataclass
class RadarItem:
    """Normalized representation of a research paper, article, or release."""

    uid: str
    title: str
    url: str
    source: str
    source_type: str = "paper"  # paper | blog | release | news | spec
    authors: str = ""
    org: str = ""
    published_at: str = ""
    fetched_at: str = ""
    abstract: str = ""
    summary: str = ""
    summary_model: str = ""
    topics: str = ""  # comma-separated string
    score: float = 0.0
    id: Optional[int] = None
    extra_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts item to a dictionary for SQLite storage."""
        d = asdict(self)
        d.pop("extra_metadata", None)
        return d


def strip_html_tags(text: str) -> str:
    """Strips HTML markup and decodes HTML entities safely."""
    if not text:
        return ""
    # Use BeautifulSoup with fast html.parser
    soup = BeautifulSoup(text, "html.parser")
    # Remove script and style elements
    for script_or_style in soup(["script", "style", "svg", "noscript"]):
        script_or_style.decompose()
    clean = soup.get_text(separator=" ")
    clean = html.unescape(clean)
    # Collapse multiple whitespaces
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def normalize_url(raw_url: str) -> str:
    """Removes marketing and tracking parameters, normalizes case and slashes."""
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url.strip())
        # Filter tracking params
        tracking_params = {
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "gclid",
            "fbclid",
            "ref",
            "source",
        }
        query_dict = parse_qs(parsed.query, keep_blank_values=False)
        clean_query_dict = {
            k: v for k, v in query_dict.items() if k.lower() not in tracking_params
        }
        clean_query = urlencode(clean_query_dict, doseq=True)

        scheme = (parsed.scheme or "https").lower()
        netloc = (parsed.netloc or "").lower()
        path = parsed.path.rstrip("/") if parsed.path != "/" else "/"

        clean_url = urlunparse((scheme, netloc, path, parsed.params, clean_query, ""))
        return clean_url
    except Exception:
        return raw_url.strip()


def extract_arxiv_id(text_or_url: str) -> Optional[str]:
    """Extracts an arXiv identifier from a URL or text string."""
    match = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+(?:v[0-9]+)?)", text_or_url)
    if match:
        arxiv_id = match.group(1)
        # strip version suffix for deduplication stability if desired
        return re.sub(r"v[0-9]+$", "", arxiv_id)
    match_num = re.search(r"\b([0-9]{4}\.[0-9]{4,5})\b", text_or_url)
    if match_num:
        return match_num.group(1)
    return None


def generate_uid(
    url: str,
    title: str = "",
    arxiv_id: Optional[str] = None,
    doi: Optional[str] = None,
) -> str:
    """Generates a stable unique identifier for deduplication."""
    clean_url = normalize_url(url)
    if not arxiv_id:
        arxiv_id = extract_arxiv_id(clean_url)

    if arxiv_id:
        return f"arxiv:{arxiv_id}"

    if doi:
        clean_doi = doi.lower().strip().replace("https://doi.org/", "")
        return f"doi:{clean_doi}"

    # GitHub release check
    gh_match = re.search(r"github\.com/([^/]+/[^/]+)/releases/tag/(.+)", clean_url)
    if gh_match:
        return f"gh:{gh_match.group(1)}:{gh_match.group(2)}"

    # Fallback to deterministic SHA-256 hash of normalized URL
    hash_digest = hashlib.sha256(clean_url.encode("utf-8")).hexdigest()[:16]
    return f"url:{hash_digest}"


def parse_iso_date(raw_date: Any) -> str:
    """Parses various date formats into an ISO 8601 UTC string."""
    if not raw_date:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if isinstance(raw_date, datetime.datetime):
        if raw_date.tzinfo is None:
            raw_date = raw_date.replace(tzinfo=datetime.timezone.utc)
        return raw_date.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        dt = date_parser.parse(str(raw_date))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
