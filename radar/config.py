"""Configuration management for Paper Radar."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


def load_yaml(path: Path) -> Dict[str, Any]:
    """Safely loads a YAML configuration file."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


class RadarConfig:
    """Consolidated configuration for Paper Radar."""

    def __init__(self, profile_override: Optional[str] = None):
        self.settings = load_yaml(CONFIG_DIR / "settings.yaml")
        self.topics = load_yaml(CONFIG_DIR / "topics.yaml").get("topics", {})
        self.sources_data = load_yaml(CONFIG_DIR / "sources.yaml").get("sources", [])

        # Environment overrides
        self.contact_email = (os.getenv("RADAR_CONTACT_EMAIL") or "").strip() or "researcher@example.com"
        self.profile = (
            profile_override
            or os.getenv("RADAR_PROFILE")
            or self.settings.get("profile", "LOCAL_LITE")
        )

        # HTTP & limits
        raw_ua = self.settings.get(
            "user_agent",
            "PaperRadar/1.0 (personal research; contact: {contact_email})",
        )
        self.user_agent = raw_ua.format(contact_email=self.contact_email)
        self.max_items_per_run = int(self.settings.get("max_items_per_run", 300))
        self.lookback_hours = int(self.settings.get("lookback_hours", 48))
        self.request_interval_seconds = float(
            self.settings.get("request_interval_seconds", 3.0)
        )
        self.timeout_seconds = float(self.settings.get("timeout_seconds", 15.0))
        self.max_response_bytes = int(self.settings.get("max_response_bytes", 2000000))

        # Storage & site paths
        db_rel = self.settings.get("db_path", "radar.db")
        self.db_path = BASE_DIR / db_rel
        site_rel = self.settings.get("site_dir", "site")
        self.site_dir = BASE_DIR / site_rel
        self.templates_dir = BASE_DIR / "templates"

        # Scoring weights
        scoring_cfg = self.settings.get("scoring", {})
        self.recency_weight = float(scoring_cfg.get("recency_weight", 0.35))
        self.authority_weight = float(scoring_cfg.get("authority_weight", 0.25))
        self.topic_weight = float(scoring_cfg.get("topic_weight", 0.25))
        self.trending_weight = float(scoring_cfg.get("trending_weight", 0.15))
        self.decay_half_life_hours = float(scoring_cfg.get("decay_half_life_hours", 72.0))

        # Summarization
        summary_cfg = self.settings.get("summary", {})
        self.summary_mode = summary_cfg.get("mode", "extractive")
        self.daily_token_cap = int(summary_cfg.get("daily_token_cap", 50000))

        # Notifications
        publish_cfg = self.settings.get("publish", {})
        self.site_visibility = publish_cfg.get("site_visibility", "public")
        self.telegram_digest_enabled = bool(publish_cfg.get("telegram_digest", True))
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    @property
    def allowlisted_domains(self) -> set[str]:
        """Returns the set of allowlisted domain names derived from sources.yaml."""
        domains = set()
        for s in self.sources_data:
            if s.get("domain"):
                domains.add(s["domain"].lower())
        # Default essential domains for radar
        domains.update(["arxiv.org", "export.arxiv.org", "huggingface.co", "github.com"])
        return domains


def get_config(profile: Optional[str] = None) -> RadarConfig:
    """Factory function for RadarConfig."""
    return RadarConfig(profile_override=profile)
