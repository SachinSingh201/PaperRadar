"""Scoring algorithm combining recency, source authority, topic relevance, and trending signals."""

from __future__ import annotations

import datetime
import math
from typing import Dict, Optional
from radar.config import RadarConfig, get_config
from radar.normalize import RadarItem, parse_iso_date


class Scorer:
    """Scores research items according to recency, authority, topic relevance, and trending signals."""

    def __init__(self, config: Optional[RadarConfig] = None):
        self.config = config or get_config()
        self.authority_map: Dict[str, float] = {}
        self._build_authority_map()

    def _build_authority_map(self) -> None:
        """Maps source IDs and organizations to authority scores."""
        tier_weights = {1: 1.0, 2: 0.7, 3: 0.4}
        for s in self.config.sources_data:
            sid = s.get("id")
            tier = s.get("authority_tier", 2)
            score = tier_weights.get(tier, 0.7)
            if sid:
                self.authority_map[sid] = score
            if s.get("org"):
                self.authority_map[s["org"].lower()] = score

    def calculate_recency(self, published_at: str, now: Optional[datetime.datetime] = None) -> float:
        """Calculates exponential recency decay: exp(-age_hours / half_life)."""
        if now is None:
            now = datetime.datetime.now(datetime.timezone.utc)

        try:
            # Parse published date
            from dateutil import parser as dparser
            pub_dt = dparser.parse(published_at)
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)
            age_hours = max(0.0, (now - pub_dt).total_seconds() / 3600.0)
        except Exception:
            age_hours = 24.0

        half_life = self.config.decay_half_life_hours
        recency = math.exp(-age_hours / half_life)
        return min(1.0, max(0.0, recency))

    def get_source_authority(self, item: RadarItem) -> float:
        """Retrieves authority score for the source or organization."""
        if item.source in self.authority_map:
            return self.authority_map[item.source]
        if item.org and item.org.lower() in self.authority_map:
            return self.authority_map[item.org.lower()]
        return 0.6  # Default medium authority

    def calculate_trending(self, item: RadarItem) -> float:
        """Calculates normalized trending score from HF upvotes or citation signals."""
        upvotes = item.extra_metadata.get("upvotes", 0)
        if isinstance(upvotes, (int, float)) and upvotes > 0:
            # e.g., 20 upvotes maps to 1.0
            return min(1.0, upvotes / 20.0)

        # Release items get a moderate trending baseline
        if item.source_type in ("release", "spec"):
            return 0.7

        return 0.2

    def score_item(
        self,
        item: RadarItem,
        topic_match_score: float = 0.5,
        now: Optional[datetime.datetime] = None,
    ) -> float:
        """Computes composite score and updates item.score."""
        recency = self.calculate_recency(item.published_at, now=now)
        authority = self.get_source_authority(item)
        trending = self.calculate_trending(item)

        w_rec = self.config.recency_weight
        w_auth = self.config.authority_weight
        w_top = self.config.topic_weight
        w_trend = self.config.trending_weight

        total = (
            w_rec * recency
            + w_auth * authority
            + w_top * topic_match_score
            + w_trend * trending
        )

        item.score = round(total, 4)
        return item.score
