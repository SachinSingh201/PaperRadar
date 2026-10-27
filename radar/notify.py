"""Digest notifications via Telegram and local formatting."""

from __future__ import annotations

import logging
from typing import List, Optional
import httpx

from radar.config import RadarConfig, get_config
from radar.normalize import RadarItem
from radar.store import Storage

logger = logging.getLogger("radar.notify")


def format_digest_markdown(items: List[RadarItem], max_items: int = 10) -> str:
    """Formats top research items into a readable markdown digest."""
    if not items:
        return "📡 *Paper Radar — Daily Digest*\n\nNo new items indexed today."

    top_items = items[:max_items]
    lines = [
        "📡 *Paper Radar — Daily Intelligence Digest*",
        f"Top {len(top_items)} papers, releases & breakthroughs for today:\n",
    ]

    for idx, item in enumerate(top_items, 1):
        org = item.org or item.source
        type_str = item.source_type.upper()
        topics_str = f" `[{item.topics}]`" if item.topics else ""

        lines.append(f"*{idx}. [{item.title}]({item.url})*")
        lines.append(f"🏷️ *{org}* • _{type_str}_{topics_str} • Score: {item.score:.2f}")

        # Summary bullets
        clean_summary = item.summary.replace("\n\n", "\n")
        lines.append(clean_summary)
        lines.append(f"🔗 [Original Link]({item.url})\n")

    return "\n".join(lines)


class Notifier:
    """Dispatches daily digest notifications."""

    def __init__(self, config: Optional[RadarConfig] = None, storage: Optional[Storage] = None):
        self.config = config or get_config()
        self.storage = storage or Storage(config=self.config)

    def send_telegram_message(self, text: str) -> bool:
        """Sends a message via Telegram Bot API."""
        token = self.config.telegram_bot_token
        chat_id = self.config.telegram_chat_id

        if not token or not chat_id:
            logger.info("Telegram notification skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured.")
            return False

        telegram_api_url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(telegram_api_url, json=payload)
                if resp.status_code == 200:
                    logger.info("Daily digest successfully delivered to Telegram!")
                    return True
                else:
                    logger.error(f"Telegram API failed ({resp.status_code}): {resp.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def send_daily_digest(self) -> str:
        """Collects today's top items and dispatches the digest."""
        items = self.storage.get_today_items(hours=self.config.lookback_hours, limit=10)
        digest_text = format_digest_markdown(items)

        if self.config.telegram_digest_enabled:
            self.send_telegram_message(digest_text)

        return digest_text
