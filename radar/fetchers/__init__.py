"""Fetcher registry and dispatcher."""

from __future__ import annotations

from typing import Any, Dict, Optional, Type
from radar.config import RadarConfig
from radar.fetchers.arxiv import ArxivFetcher
from radar.fetchers.base import BaseFetcher
from radar.fetchers.github_releases import GithubReleasesFetcher
from radar.fetchers.huggingface import HuggingFaceFetcher
from radar.fetchers.rss import RssFetcher
from radar.polite_http import PoliteHttpClient

FETCHER_MAP: Dict[str, Type[BaseFetcher]] = {
    "arxiv": ArxivFetcher,
    "rss": RssFetcher,
    "huggingface": HuggingFaceFetcher,
    "github_release": GithubReleasesFetcher,
}


def get_fetcher_for_source(
    source_info: Dict[str, Any],
    config: Optional[RadarConfig] = None,
    http_client: Optional[PoliteHttpClient] = None,
) -> Optional[BaseFetcher]:
    """Instantiates the appropriate fetcher based on source 'method'."""
    method = source_info.get("method", "rss").lower()
    fetcher_cls = FETCHER_MAP.get(method, RssFetcher)
    return fetcher_cls(config=config, http_client=http_client)
