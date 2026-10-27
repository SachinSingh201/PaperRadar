"""SQLite storage layer with FTS5 full-text search and bookmarking support."""

from __future__ import annotations

import datetime
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from radar.config import RadarConfig, get_config
from radar.normalize import RadarItem

logger = logging.getLogger("radar.store")


class Storage:
    """Manages SQLite database, full-text search indexing, and local bookmarks."""

    def __init__(self, db_path: Optional[Path | str] = None, config: Optional[RadarConfig] = None):
        self.config = config or get_config()
        self.db_path = Path(db_path) if db_path else self.config.db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a configured SQLite connection with foreign keys enabled."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        """Initializes database tables, triggers, and FTS5 search index."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._get_connection() as conn:
            # 1. Main items table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                  id            INTEGER PRIMARY KEY AUTOINCREMENT,
                  uid           TEXT UNIQUE,
                  title         TEXT NOT NULL,
                  authors       TEXT,
                  org           TEXT,
                  source        TEXT,
                  source_type   TEXT,
                  url           TEXT NOT NULL,
                  published_at  TEXT,
                  fetched_at    TEXT,
                  abstract      TEXT,
                  summary       TEXT,
                  summary_model TEXT,
                  topics        TEXT,
                  score         REAL DEFAULT 0
                );
                """
            )

            # 2. Virtual FTS5 table
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
                  title,
                  abstract,
                  summary,
                  topics,
                  content='items',
                  content_rowid='id'
                );
                """
            )

            # 3. Triggers for FTS5 synchronization
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS items_ai AFTER INSERT ON items BEGIN
                  INSERT INTO items_fts(rowid, title, abstract, summary, topics)
                  VALUES (new.id, new.title, new.abstract, new.summary, new.topics);
                END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS items_ad AFTER DELETE ON items BEGIN
                  INSERT INTO items_fts(items_fts, rowid, title, abstract, summary, topics)
                  VALUES ('delete', old.id, old.title, old.abstract, old.summary, old.topics);
                END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS items_au AFTER UPDATE ON items BEGIN
                  INSERT INTO items_fts(items_fts, rowid, title, abstract, summary, topics)
                  VALUES ('delete', old.id, old.title, old.abstract, old.summary, old.topics);
                  INSERT INTO items_fts(rowid, title, abstract, summary, topics)
                  VALUES (new.id, new.title, new.abstract, new.summary, new.topics);
                END;
                """
            )

            # 4. Fetch log and robots cache
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fetch_log (
                  source TEXT,
                  fetched_at TEXT,
                  status INTEGER,
                  etag TEXT,
                  last_modified TEXT,
                  items_added INTEGER
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS robots_cache (
                  domain TEXT PRIMARY KEY,
                  body TEXT,
                  fetched_at TEXT
                );
                """
            )

            # 5. Local bookmarks (excluded from public build)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bookmarks (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  item_id INTEGER,
                  note TEXT,
                  status TEXT,
                  created_at TEXT,
                  FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
                );
                """
            )

    def row_to_item(self, row: sqlite3.Row) -> RadarItem:
        """Converts an SQLite row to a RadarItem object."""
        return RadarItem(
            id=row["id"],
            uid=row["uid"],
            title=row["title"],
            authors=row["authors"] or "",
            org=row["org"] or "",
            source=row["source"] or "",
            source_type=row["source_type"] or "paper",
            url=row["url"],
            published_at=row["published_at"] or "",
            fetched_at=row["fetched_at"] or "",
            abstract=row["abstract"] or "",
            summary=row["summary"] or "",
            summary_model=row["summary_model"] or "",
            topics=row["topics"] or "",
            score=float(row["score"] or 0.0),
        )

    def insert_items(self, items: List[RadarItem]) -> int:
        """Inserts unique items into the database, ignoring duplicates. Returns count added."""
        if not items:
            return 0

        inserted_count = 0
        with self._get_connection() as conn:
            for item in items:
                try:
                    conn.execute(
                        """
                        INSERT INTO items (
                            uid, title, authors, org, source, source_type,
                            url, published_at, fetched_at, abstract, summary,
                            summary_model, topics, score
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item.uid,
                            item.title,
                            item.authors,
                            item.org,
                            item.source,
                            item.source_type,
                            item.url,
                            item.published_at,
                            item.fetched_at,
                            item.abstract,
                            item.summary,
                            item.summary_model,
                            item.topics,
                            item.score,
                        ),
                    )
                    inserted_count += 1
                except sqlite3.IntegrityError:
                    # Item already exists by UID, skip or update score if higher
                    continue

        return inserted_count

    def get_all_items(self, limit: int = 500) -> List[RadarItem]:
        """Retrieves items ordered by score descending."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM items ORDER BY score DESC, published_at DESC LIMIT ?",
                (limit,),
            )
            return [self.row_to_item(r) for r in cursor.fetchall()]

    def get_today_items(self, hours: int = 48, limit: int = 50) -> List[RadarItem]:
        """Retrieves items published within lookback hours ordered by score."""
        cutoff = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM items
                WHERE published_at >= ?
                ORDER BY score DESC, published_at DESC
                LIMIT ?
                """,
                (cutoff, limit),
            )
            results = [self.row_to_item(r) for r in cursor.fetchall()]

        # Fallback to top items if database has items older than cutoff (e.g. backfilled or offline demo)
        if not results:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM items ORDER BY score DESC, published_at DESC LIMIT ?",
                    (limit,),
                )
                results = [self.row_to_item(r) for r in cursor.fetchall()]

        return results

    def get_week_items(self, limit: int = 100) -> List[RadarItem]:
        """Retrieves top items from the past 7 days."""
        cutoff = (
            datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM items
                WHERE published_at >= ?
                ORDER BY score DESC, published_at DESC
                LIMIT ?
                """,
                (cutoff, limit),
            )
            results = [self.row_to_item(r) for r in cursor.fetchall()]

        if not results:
            results = self.get_all_items(limit=limit)

        return results

    def search_fts(self, query: str, limit: int = 50) -> List[RadarItem]:
        """Full-text search using FTS5 virtual table."""
        if not query.strip():
            return []

        # Sanitize query for FTS5 (strip special operators)
        clean_q = "".join(c for c in query if c.isalnum() or c in (" ", "-", "_")).strip()
        if not clean_q:
            return []

        fts_query = f'"{clean_q}"'

        with self._get_connection() as conn:
            try:
                cursor = conn.execute(
                    """
                    SELECT items.* FROM items_fts
                    JOIN items ON items.id = items_fts.rowid
                    WHERE items_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, limit),
                )
                return [self.row_to_item(r) for r in cursor.fetchall()]
            except sqlite3.OperationalError:
                # Fallback to LIKE if syntax issue
                cursor = conn.execute(
                    """
                    SELECT * FROM items
                    WHERE title LIKE ? OR abstract LIKE ? OR topics LIKE ?
                    ORDER BY score DESC LIMIT ?
                    """,
                    (f"%{clean_q}%", f"%{clean_q}%", f"%{clean_q}%", limit),
                )
                return [self.row_to_item(r) for r in cursor.fetchall()]

    def record_fetch_log(
        self,
        source: str,
        status: int,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        items_added: int = 0,
    ) -> None:
        """Records an HTTP fetch operation."""
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO fetch_log (source, fetched_at, status, etag, last_modified, items_added)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (source, now, status, etag, last_modified, items_added),
            )

    def get_last_fetch(self, source: str) -> Optional[Dict[str, Any]]:
        """Retrieves the latest fetch log entry for conditional requests."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM fetch_log WHERE source = ? ORDER BY fetched_at DESC LIMIT 1",
                (source,),
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def add_bookmark(self, item_id: int, note: str = "", status: str = "unread") -> int:
        """Adds a local-only bookmark for a research paper."""
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO bookmarks (item_id, note, status, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (item_id, note, status, now),
            )
            return cursor.lastrowid or 0

    def get_bookmarks(self) -> List[Dict[str, Any]]:
        """Retrieves bookmarks with attached item metadata."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT bookmarks.id as bookmark_id, bookmarks.note, bookmarks.status, bookmarks.created_at,
                       items.*
                FROM bookmarks
                JOIN items ON items.id = bookmarks.item_id
                ORDER BY bookmarks.created_at DESC
                """
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Computes aggregate repository statistics."""
        with self._get_connection() as conn:
            total_items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
            total_sources = conn.execute("SELECT COUNT(DISTINCT source) FROM items").fetchone()[0]
            total_bookmarks = conn.execute("SELECT COUNT(*) FROM bookmarks").fetchone()[0]
            last_item = conn.execute("SELECT MAX(fetched_at) FROM items").fetchone()[0]

            # Topic breakdown
            topics_rows = conn.execute("SELECT topics FROM items WHERE topics != ''").fetchall()
            topic_counts: Dict[str, int] = {}
            for row in topics_rows:
                for t in row[0].split(","):
                    t = t.strip()
                    if t:
                        topic_counts[t] = topic_counts.get(t, 0) + 1

        return {
            "total_items": total_items,
            "total_sources": total_sources,
            "total_bookmarks": total_bookmarks,
            "last_fetched_at": last_item or "Never",
            "topic_counts": dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)),
        }
