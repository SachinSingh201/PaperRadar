"""Static site generator rendering Jinja2 templates into standalone HTML."""

from __future__ import annotations

import datetime
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from radar.config import RadarConfig, get_config
from radar.normalize import RadarItem
from radar.store import Storage

logger = logging.getLogger("radar.publish_site")

CSS_CONTENT = """/* Paper Radar — Modern Design System */
:root {
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;

  /* Dark Theme Tokens (Default) */
  --bg-main: #090d16;
  --bg-card: rgba(16, 24, 40, 0.72);
  --bg-card-hover: rgba(23, 34, 58, 0.85);
  --bg-header: rgba(9, 13, 22, 0.85);
  --border-card: rgba(255, 255, 255, 0.08);
  --border-card-hover: rgba(56, 189, 248, 0.35);

  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --text-dim: #64748b;

  --accent-cyan: #38bdf8;
  --accent-indigo: #818cf8;
  --accent-emerald: #34d399;
  --accent-amber: #fbbf24;
  --accent-rose: #f43f5e;

  --primary-gradient: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
  --glow-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
}

[data-theme="light"] {
  --bg-main: #f8fafc;
  --bg-card: rgba(255, 255, 255, 0.88);
  --bg-card-hover: #ffffff;
  --bg-header: rgba(255, 255, 255, 0.88);
  --border-card: rgba(0, 0, 0, 0.08);
  --border-card-hover: rgba(56, 189, 248, 0.5);

  --text-main: #0f172a;
  --text-muted: #475569;
  --text-dim: #94a3b8;

  --glow-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-sans);
  background-color: var(--bg-main);
  color: var(--text-main);
  line-height: 1.6;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  transition: background-color 0.25s ease, color 0.25s ease;
  overflow-x: hidden;
}

.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
}

/* Header */
.site-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: var(--bg-header);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-card);
  padding: 16px 0;
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  font-weight: 700;
  font-size: 1.25rem;
  color: var(--text-main);
}

.logo-radar {
  font-size: 1.4rem;
  animation: pulse 2.5s infinite ease-in-out;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.85; }
}

.badge-profile {
  font-size: 0.72rem;
  padding: 3px 8px;
  border-radius: 9999px;
  background: var(--primary-gradient);
  color: #ffffff;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.main-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.nav-link {
  color: var(--text-muted);
  text-decoration: none;
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  font-size: 0.92rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: var(--text-main);
  background: rgba(255, 255, 255, 0.05);
}

.nav-link.active {
  color: var(--accent-cyan);
  background: rgba(56, 189, 248, 0.1);
  font-weight: 600;
}

.theme-toggle {
  background: transparent;
  border: 1px solid var(--border-card);
  color: var(--text-main);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  cursor: pointer;
  font-size: 1.1rem;
  transition: all 0.2s ease;
}

.theme-toggle:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: var(--accent-cyan);
}

/* Hero Section */
.hero-section {
  padding: 48px 0 32px 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-pill {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 9999px;
  font-size: 0.82rem;
  font-weight: 600;
  background: rgba(56, 189, 248, 0.12);
  color: var(--accent-cyan);
  border: 1px solid rgba(56, 189, 248, 0.25);
  width: fit-content;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.2;
}

.hero-subtitle {
  color: var(--text-muted);
  font-size: 1.1rem;
  max-width: 720px;
}

.stats-ribbon {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
  margin-top: 8px;
}

.stat-box {
  background: var(--bg-card);
  backdrop-filter: blur(12px);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--glow-shadow);
}

.stat-number {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--accent-cyan);
}

.stat-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Quick Filters */
.quick-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 24px;
}

.filter-label {
  font-size: 0.85rem;
  color: var(--text-dim);
  font-weight: 600;
}

.filter-chip {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  color: var(--text-muted);
  padding: 6px 14px;
  border-radius: 9999px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-chip:hover, .filter-chip.active {
  background: var(--accent-cyan);
  color: #090d16;
  border-color: var(--accent-cyan);
  font-weight: 600;
}

/* Items Grid */
.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 24px;
  margin-bottom: 48px;
}

/* Radar Card */
.radar-card {
  background: var(--bg-card);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: var(--glow-shadow);
  transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
  position: relative;
}

.radar-card:hover {
  transform: translateY(-3px);
  border-color: var(--border-card-hover);
  box-shadow: 0 12px 36px 0 rgba(56, 189, 248, 0.12);
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-meta-top {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.card-score-box {
  display: flex;
  align-items: center;
  gap: 4px;
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(251, 191, 36, 0.3);
  padding: 2px 8px;
  border-radius: 9999px;
}

.score-icon {
  color: var(--accent-amber);
  font-size: 0.85rem;
}

.score-val {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--accent-amber);
  font-family: var(--font-mono);
}

/* Badges */
.badge {
  font-size: 0.75rem;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  letter-spacing: 0.3px;
}

.badge-source {
  background: rgba(129, 140, 248, 0.15);
  color: var(--accent-indigo);
  border: 1px solid rgba(129, 140, 248, 0.3);
}

.badge-type {
  text-transform: uppercase;
}

.badge-type-paper {
  background: rgba(56, 189, 248, 0.12);
  color: var(--accent-cyan);
  border: 1px solid rgba(56, 189, 248, 0.25);
}

.badge-type-release {
  background: rgba(52, 211, 153, 0.12);
  color: var(--accent-emerald);
  border: 1px solid rgba(52, 211, 153, 0.25);
}

.badge-type-spec {
  background: rgba(244, 63, 94, 0.12);
  color: var(--accent-rose);
  border: 1px solid rgba(244, 63, 94, 0.25);
}

.badge-type-blog {
  background: rgba(251, 191, 36, 0.12);
  color: var(--accent-amber);
  border: 1px solid rgba(251, 191, 36, 0.25);
}

.card-date {
  font-size: 0.78rem;
  color: var(--text-dim);
}

.card-title {
  font-size: 1.15rem;
  font-weight: 700;
  line-height: 1.4;
}

.card-title a {
  color: var(--text-main);
  text-decoration: none;
  transition: color 0.2s ease;
}

.card-title a:hover {
  color: var(--accent-cyan);
}

.card-authors {
  font-size: 0.82rem;
  color: var(--text-dim);
  font-style: italic;
}

.card-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag-pill {
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-muted);
  text-decoration: none;
  border: 1px solid var(--border-card);
  transition: all 0.2s ease;
}

.tag-pill:hover {
  background: rgba(56, 189, 248, 0.15);
  color: var(--accent-cyan);
  border-color: var(--accent-cyan);
}

.card-summary {
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  font-size: 0.88rem;
  color: var(--text-muted);
  border-left: 3px solid var(--accent-cyan);
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: auto;
  padding-top: 8px;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: var(--radius-sm);
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease;
}

.btn-primary {
  background: var(--primary-gradient);
  color: #ffffff;
  border: none;
}

.btn-primary:hover {
  opacity: 0.92;
  transform: translateY(-1px);
}

.btn-secondary {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border-card);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-main);
  border-color: var(--accent-amber);
}

/* Topic & Org Navigation */
.topic-navigation {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 32px;
}

.topic-nav-pill {
  padding: 8px 16px;
  border-radius: 9999px;
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  color: var(--text-muted);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.topic-nav-pill:hover {
  border-color: var(--accent-cyan);
  color: var(--text-main);
}

.pill-count {
  font-size: 0.72rem;
  background: rgba(56, 189, 248, 0.2);
  color: var(--accent-cyan);
  padding: 2px 6px;
  border-radius: 9999px;
  margin-left: 4px;
}

.topic-group-section {
  margin-bottom: 48px;
  scroll-margin-top: 100px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-card);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 800;
}

/* Search Interface */
.search-bar-wrapper {
  position: relative;
  width: 100%;
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
  padding: 16px 48px 16px 20px;
  font-size: 1.05rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-card);
  background: var(--bg-card);
  color: var(--text-main);
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.search-input:focus {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2);
}

.search-clear-btn {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 1.2rem;
  cursor: pointer;
}

.search-filters {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.filter-select {
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  color: var(--text-main);
  border: 1px solid var(--border-card);
  outline: none;
}

.search-status {
  font-size: 0.9rem;
  color: var(--text-muted);
  margin-bottom: 20px;
}

/* About & Sources Table */
.about-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 32px;
  margin-bottom: 24px;
}

.about-card h2 {
  font-size: 1.4rem;
  margin-bottom: 16px;
  color: var(--accent-cyan);
}

.about-card p, .about-card ul {
  color: var(--text-muted);
  margin-bottom: 16px;
}

.about-card ul {
  padding-left: 20px;
}

.sources-table-wrapper {
  overflow-x: auto;
  margin-top: 16px;
}

.sources-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.sources-table th, .sources-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-card);
}

.sources-table th {
  color: var(--text-dim);
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.75rem;
}

.sources-table td a {
  color: var(--accent-cyan);
  text-decoration: none;
}

/* Footer */
.site-footer {
  margin-top: auto;
  border-top: 1px solid var(--border-card);
  padding: 32px 0;
  background: var(--bg-card);
  font-size: 0.85rem;
}

.footer-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.footer-badges {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.badge-subtle {
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-dim);
  border: 1px solid var(--border-card);
}

@media (max-width: 768px) {
  .items-grid {
    grid-template-columns: 1fr;
  }
  .hero-title {
    font-size: 1.85rem;
  }
}
"""

JS_CONTENT = """// Paper Radar — Client-side Search, Filtering, and Bookmarks
document.addEventListener('DOMContentLoaded', () => {
  // Theme Toggle
  const themeToggle = document.getElementById('theme-toggle');
  const html = document.documentElement;
  const savedTheme = localStorage.getItem('radar_theme') || 'dark';
  html.setAttribute('data-theme', savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = html.getAttribute('data-theme');
      const target = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', target);
      localStorage.setItem('radar_theme', target);
    });
  }

  // Quick Filter Chips (Today/Index page)
  const filterChips = document.querySelectorAll('.filter-chip');
  const cards = document.querySelectorAll('.radar-card');

  filterChips.forEach(chip => {
    chip.addEventListener('click', () => {
      filterChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      const filterType = chip.getAttribute('data-filter');

      cards.forEach(card => {
        const cardType = card.getAttribute('data-type');
        if (filterType === 'all' || cardType === filterType) {
          card.style.display = 'flex';
        } else {
          card.style.display = 'none';
        }
      });
    });
  });

  // Client-side Search (Search page)
  const searchInput = document.getElementById('search-input');
  const clearBtn = document.getElementById('search-clear');
  const typeFilter = document.getElementById('filter-type');
  const sortFilter = document.getElementById('filter-sort');
  const searchCards = document.querySelectorAll('.search-card');
  const resultsCount = document.getElementById('results-count');

  function runSearch() {
    if (!searchInput) return;
    const query = searchInput.value.toLowerCase().trim();
    const selectedType = typeFilter ? typeFilter.value : '';
    let visibleCount = 0;

    searchCards.forEach(card => {
      const title = (card.querySelector('.card-title') || {}).innerText?.toLowerCase() || '';
      const summary = (card.querySelector('.card-summary') || {}).innerText?.toLowerCase() || '';
      const topics = (card.getAttribute('data-topics') || '').toLowerCase();
      const cardType = card.getAttribute('data-type') || '';

      const matchesQuery = !query || title.includes(query) || summary.includes(query) || topics.includes(query);
      const matchesType = !selectedType || cardType === selectedType;

      if (matchesQuery && matchesType) {
        card.style.display = 'flex';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    if (resultsCount) {
      resultsCount.innerText = visibleCount;
    }
  }

  if (searchInput) {
    searchInput.addEventListener('input', runSearch);
  }
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (searchInput) searchInput.value = '';
      runSearch();
    });
  }
  if (typeFilter) {
    typeFilter.addEventListener('change', runSearch);
  }

  // Bookmarking in Client LocalStorage
  const bookmarkButtons = document.querySelectorAll('.bookmark-btn');
  let savedBookmarks = JSON.parse(localStorage.getItem('radar_client_bookmarks') || '{}');

  function updateBookmarkUI() {
    bookmarkButtons.forEach(btn => {
      const uid = btn.getAttribute('data-uid');
      if (savedBookmarks[uid]) {
        btn.innerText = '★ Bookmarked';
        btn.classList.add('btn-bookmarked');
      } else {
        btn.innerText = '⭐ Bookmark';
        btn.classList.remove('btn-bookmarked');
      }
    });
  }

  bookmarkButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const uid = btn.getAttribute('data-uid');
      const title = btn.getAttribute('data-title');
      if (savedBookmarks[uid]) {
        delete savedBookmarks[uid];
      } else {
        savedBookmarks[uid] = { title, savedAt: new Date().toISOString() };
      }
      localStorage.setItem('radar_client_bookmarks', JSON.stringify(savedBookmarks));
      updateBookmarkUI();
    });
  });

  updateBookmarkUI();
});
"""


class SitePublisher:
    """Generates the static HTML website and RSS feed."""

    def __init__(self, config: Optional[RadarConfig] = None, storage: Optional[Storage] = None):
        self.config = config or get_config()
        self.storage = storage or Storage(config=self.config)
        self.templates_dir = self.config.templates_dir
        self.site_dir = self.config.site_dir
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def build(self) -> None:
        """Renders all static site pages, search index, RSS feed, and assets."""
        self.site_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Building static website into: {self.site_dir}")

        # Fetch data
        all_items = self.storage.get_all_items(limit=300)
        today_items = self.storage.get_today_items(hours=self.config.lookback_hours, limit=50)
        week_items = self.storage.get_week_items(limit=100)
        stats = self.storage.get_stats()

        # Group items by topic
        topic_groups: Dict[str, List[RadarItem]] = {}
        for t in self.config.topics.keys():
            matching = [it for it in all_items if t in it.topics.split(",")]
            if matching:
                topic_groups[t] = matching

        # Group items by organization
        org_groups: Dict[str, List[RadarItem]] = {}
        for it in all_items:
            org = it.org or "Other"
            if org not in org_groups:
                org_groups[org] = []
            org_groups[org].append(it)

        # Sort org groups by size
        org_groups = dict(sorted(org_groups.items(), key=lambda x: len(x[1]), reverse=True))

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        build_time_str = now_utc.strftime("%Y-%m-%d %H:%M:%S")
        build_time_rfc = now_utc.strftime("%a, %d %b %Y %H:%M:%S GMT")

        common_ctx = {
            "profile": self.config.profile,
            "total_items": stats["total_items"],
            "total_sources": len(self.config.sources_data),
            "top_topics": list(topic_groups.keys()),
            "build_time": build_time_str,
            "build_time_rfc": build_time_rfc,
            "site_url": "https://localhost:8000",
            "sources_list": self.config.sources_data,
        }

        # 1. Render Index (Today)
        self._render_page(
            "today.html",
            "index.html",
            {**common_ctx, "items": today_items, "active_page": "today"},
        )

        # 2. Render This Week
        self._render_page(
            "week.html",
            "week.html",
            {**common_ctx, "items": week_items, "active_page": "week"},
        )

        # 3. Render Topics
        self._render_page(
            "topics.html",
            "topics.html",
            {**common_ctx, "topic_groups": topic_groups, "active_page": "topics"},
        )

        # 4. Render Organizations
        self._render_page(
            "organizations.html",
            "organizations.html",
            {**common_ctx, "org_groups": org_groups, "active_page": "orgs"},
        )

        # 5. Render Search
        self._render_page(
            "search.html",
            "search.html",
            {**common_ctx, "items": all_items, "active_page": "search"},
        )

        # 6. Render About
        self._render_page(
            "about.html",
            "about.html",
            {**common_ctx, "active_page": "about"},
        )

        # 7. Render RSS Feed
        self._render_page(
            "feed.xml",
            "feed.xml",
            {**common_ctx, "items": today_items or all_items},
        )

        # 8. Export search index JSON
        search_index_path = self.site_dir / "search_index.json"
        search_records = [it.to_dict() for it in all_items]
        with open(search_index_path, "w", encoding="utf-8") as f:
            json.dump(search_records, f, indent=2)

        # 9. Write CSS and JS assets
        with open(self.site_dir / "style.css", "w", encoding="utf-8") as f:
            f.write(CSS_CONTENT)

        with open(self.site_dir / "app.js", "w", encoding="utf-8") as f:
            f.write(JS_CONTENT)

        logger.info(f"Static site successfully built with {len(all_items)} total indexed items!")

    def _render_page(self, template_name: str, output_name: str, context: Dict[str, Any]) -> None:
        """Renders a single template and writes to output file."""
        template = self.jinja_env.get_template(template_name)
        rendered = template.render(**context)
        out_path = self.site_dir / output_name
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(rendered)
