"""Command-line interface for Paper Radar."""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Optional

# Ensure UTF-8 output on Windows terminals
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from radar.config import get_config
from radar.pipeline import Pipeline
from radar.publish_site import SitePublisher
from radar.store import Storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("radar.cli")


def build_parser() -> argparse.ArgumentParser:
    """Builds argument parser for radar CLI commands."""
    parser = argparse.ArgumentParser(
        prog="radar",
        description="Paper Radar — Automated, safe AI research intelligence pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run the full pipeline (fetch, score, summarize, build site)")
    run_parser.add_argument("--profile", choices=["LOCAL_LITE", "LOCAL_PLUS", "CLOUD"], help="Run profile")
    run_parser.add_argument("--sources", nargs="*", help="Filter to specific source IDs")
    run_parser.add_argument("--backfill", action="store_true", help="Fetch older historical items beyond the lookback window")
    run_parser.add_argument("--skip-site", action="store_true", help="Skip static site regeneration")
    run_parser.add_argument("--skip-notify", action="store_true", help="Skip daily notifications")

    # Command: fetch
    fetch_parser = subparsers.add_parser("fetch", help="Fetch and process items from sources into the database")
    fetch_parser.add_argument("--sources", nargs="*", help="Specific source IDs to fetch")
    fetch_parser.add_argument("--backfill", action="store_true", help="Fetch older historical items beyond the lookback window")
    fetch_parser.add_argument("--limit", type=int, help="Maximum items to fetch")

    # Command: build
    subparsers.add_parser("build", help="Build the static website and search index from existing database")

    # Command: search
    search_parser = subparsers.add_parser("search", help="Search the database using SQLite FTS5")
    search_parser.add_argument("query", help="Search terms or keywords")
    search_parser.add_argument("--limit", type=int, default=10, help="Max results to display")

    # Command: stats
    subparsers.add_parser("stats", help="Show database metrics and topic breakdown")

    # Command: notify
    subparsers.add_parser("notify", help="Generate and send daily digest")

    # Command: bookmark
    bm_parser = subparsers.add_parser("bookmark", help="Bookmark an item in the local private database")
    bm_parser.add_argument("item_id", type=int, help="Item ID to bookmark")
    bm_parser.add_argument("--note", default="", help="Personal reading note")

    # Command: bookmarks
    subparsers.add_parser("bookmarks", help="List saved personal bookmarks")

    return parser


def main(args: Optional[list] = None) -> int:
    """Entry point for the CLI."""
    parser = build_parser()
    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 0

    config = get_config(profile=getattr(parsed, "profile", None))
    pipeline = Pipeline(config=config)

    if parsed.command == "run":
        res = pipeline.run_full_pipeline(
            source_filter=parsed.sources,
            backfill=parsed.backfill,
            skip_site=parsed.skip_site,
            skip_notify=parsed.skip_notify,
        )
        print("\n=== Run Summary ===")
        print(f"Items fetched: {res['raw_fetched']}")
        print(f"New items stored: {res['new_stored']}")
        print(f"Elapsed time: {res['duration_seconds']}s")
        return 0

    elif parsed.command == "fetch":
        raw = pipeline.run_fetch(source_filter=parsed.sources, max_items=parsed.limit, backfill=parsed.backfill)
        processed = pipeline.process_items(raw)
        inserted = pipeline.storage.insert_items(processed)
        print(f"Fetched {len(raw)} items, stored {inserted} new items.")
        return 0

    elif parsed.command == "build":
        publisher = SitePublisher(config=config)
        publisher.build()
        print(f"Static website built successfully into: {config.site_dir}")
        return 0

    elif parsed.command == "search":
        storage = Storage(config=config)
        results = storage.search_fts(parsed.query, limit=parsed.limit)
        print(f"\n--- Search results for '{parsed.query}' ({len(results)} matches) ---")
        for item in results:
            print(f"\n[{item.id}] {item.title}")
            print(f"     Source: {item.org or item.source} | Score: {item.score:.2f} | Tags: {item.topics}")
            print(f"     Link:   {item.url}")
        return 0

    elif parsed.command == "stats":
        storage = Storage(config=config)
        st = storage.get_stats()
        print("\n--- Paper Radar Stats ---")
        print(f"Total items indexed:  {st['total_items']}")
        print(f"Active sources:       {st['total_sources']}")
        print(f"Local bookmarks:      {st['total_bookmarks']}")
        print(f"Last fetched:         {st['last_fetched_at']}")
        print("\nTop Topics:")
        for t, count in list(st["topic_counts"].items())[:8]:
            print(f"  * #{t:<14}: {count} items")
        return 0

    elif parsed.command == "notify":
        digest = pipeline.notifier.send_daily_digest()
        print("\n" + digest)
        return 0

    elif parsed.command == "bookmark":
        storage = Storage(config=config)
        bm_id = storage.add_bookmark(parsed.item_id, note=parsed.note)
        print(f"Bookmarked item #{parsed.item_id} (Bookmark ID: {bm_id})")
        return 0

    elif parsed.command == "bookmarks":
        storage = Storage(config=config)
        bms = storage.get_bookmarks()
        print(f"\n--- Saved Bookmarks ({len(bms)}) ---")
        for b in bms:
            print(f"[{b['bookmark_id']}] {b['title']}")
            if b['note']:
                print(f"     Note: {b['note']}")
            print(f"     Link: {b['url']}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
