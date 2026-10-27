"""End-to-end pipeline orchestrator for Paper Radar."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional
from radar.classify import Classifier
from radar.config import RadarConfig, get_config
from radar.dedupe import Deduplicator
from radar.fetchers import get_fetcher_for_source
from radar.normalize import RadarItem
from radar.notify import Notifier
from radar.polite_http import PoliteHttpClient
from radar.publish_site import SitePublisher
from radar.score import Scorer
from radar.store import Storage
from radar.summarize import Summarizer

logger = logging.getLogger("radar.pipeline")


class Pipeline:
    """Coordinates fetching, deduplicating, classifying, scoring, summarizing, and publishing."""

    def __init__(self, config: Optional[RadarConfig] = None):
        self.config = config or get_config()
        self.storage = Storage(config=self.config)
        self.http_client = PoliteHttpClient(config=self.config)
        self.classifier = Classifier(config=self.config)
        self.scorer = Scorer(config=self.config)
        self.summarizer = Summarizer(config=self.config)
        self.publisher = SitePublisher(config=self.config, storage=self.storage)
        self.notifier = Notifier(config=self.config, storage=self.storage)

    def run_fetch(
        self,
        source_filter: Optional[List[str]] = None,
        max_items: Optional[int] = None,
        backfill: bool = False,
        max_per_source: int = 25,
    ) -> List[RadarItem]:
        """Runs the collection stage across configured sources."""
        all_raw_items: List[RadarItem] = []
        limit = max_items or self.config.max_items_per_run
        sources = self.config.sources_data

        if source_filter:
            sources = [s for s in sources if s.get("id") in source_filter]

        logger.info(f"Starting fetch across {len(sources)} sources (limit: {limit} items, backfill={backfill})...")

        cutoff_iso = ""
        if not backfill:
            import datetime
            cutoff_dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=self.config.lookback_hours)
            cutoff_iso = cutoff_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        for source in sources:
            if not source.get("enabled", True):
                continue

            sid = source.get("id", "unknown")
            fetcher = get_fetcher_for_source(source, config=self.config, http_client=self.http_client)
            if not fetcher:
                logger.warning(f"No fetcher available for source: {sid}")
                continue

            try:
                items = fetcher.fetch(source)
                
                # Apply lookback filter unless backfilling
                if cutoff_iso:
                    recent_items = [it for it in items if not it.published_at or it.published_at >= cutoff_iso]
                    # If all items were filtered out (e.g. source posts irregularly), keep top few recent items
                    items = recent_items if recent_items else items[:5]

                # Cap per source to maintain diversity
                items = items[:max_per_source]

                logger.info(f"Source [{sid}] yielded {len(items)} items")
                self.storage.record_fetch_log(source=sid, status=200, items_added=len(items))
                all_raw_items.extend(items)
            except Exception as e:
                logger.error(f"Error fetching source [{sid}]: {e}")
                self.storage.record_fetch_log(source=sid, status=500, items_added=0)

            if len(all_raw_items) >= limit:
                logger.info(f"Reached max items limit ({limit}), stopping fetch.")
                all_raw_items = all_raw_items[:limit]
                break

        return all_raw_items

    def process_items(self, raw_items: List[RadarItem]) -> List[RadarItem]:
        """Deduplicates, classifies, scores, and summarizes a list of fetched items."""
        # 1. Deduplication against database and current batch
        existing_items = self.storage.get_all_items(limit=1000)
        deduper = Deduplicator(fuzzy_threshold=90.0)
        deduper.register_existing(existing_items)

        unique_items = deduper.filter_batch(raw_items)
        logger.info(f"Filtered {len(raw_items)} raw items down to {len(unique_items)} unique items")

        processed: List[RadarItem] = []
        for item in unique_items:
            # 2. Classification
            topics, topic_score = self.classifier.classify_item(item)

            # 3. Scoring
            self.scorer.score_item(item, topic_match_score=topic_score)

            # 4. Summarization with prompt-injection defense
            self.summarizer.summarize(item)

            processed.append(item)

        return processed

    def run_full_pipeline(
        self,
        source_filter: Optional[List[str]] = None,
        backfill: bool = False,
        skip_site: bool = False,
        skip_notify: bool = False,
    ) -> Dict[str, Any]:
        """Executes the full end-to-end radar pipeline."""
        start_time = time.time()
        logger.info(f"=== PAPER RADAR PIPELINE STARTED [Profile: {self.config.profile}] ===")

        # 1. Fetch
        raw_items = self.run_fetch(source_filter=source_filter, backfill=backfill)

        # 2. Dedupe, Classify, Score, Summarize
        processed_items = self.process_items(raw_items)

        # 3. Store in SQLite + FTS5
        inserted = self.storage.insert_items(processed_items)
        logger.info(f"Stored {inserted} newly indexed items into SQLite")

        # 4. Publish static site
        if not skip_site:
            self.publisher.build()

        # 5. Notify
        digest_summary = ""
        if not skip_notify:
            digest_summary = self.notifier.send_daily_digest()

        duration = time.time() - start_time
        logger.info(f"=== PIPELINE COMPLETED IN {duration:.2f}s ===")

        return {
            "raw_fetched": len(raw_items),
            "new_stored": inserted,
            "duration_seconds": round(duration, 2),
            "digest_summary": digest_summary,
        }
