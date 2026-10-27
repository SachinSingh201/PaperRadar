"""Base fetcher interface for all data sources."""

from __future__ import annotations

import abc
import datetime
from typing import Any, Dict, List, Optional
from radar.config import RadarConfig, get_config
from radar.normalize import RadarItem
from radar.polite_http import PoliteHttpClient


class BaseFetcher(abc.ABC):
    """Abstract base class for data fetchers."""

    def __init__(
        self,
        config: Optional[RadarConfig] = None,
        http_client: Optional[PoliteHttpClient] = None,
    ):
        self.config = config or get_config()
        self.http_client = http_client or PoliteHttpClient(config=self.config)

    @abc.abstractmethod
    def fetch(self, source_info: Dict[str, Any]) -> List[RadarItem]:
        """Fetches items for the specified source.

        Args:
            source_info: Dictionary containing source configuration (id, url, name, etc.)

        Returns:
            List of normalized RadarItem objects.
        """
        raise NotImplementedError
