# 📡 Paper Radar

[![Tests](https://img.shields.io/badge/tests-20%20passed-brightgreen.svg)](#testing)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Zero Trackers](https://img.shields.io/badge/trackers-zero-success.svg)](#security-and-ethics)

A lightweight, ethical, low-cost system that tracks the latest AI research papers, lab blog posts, and release announcements (RAG, LLMs, agents, MCP, evaluation, multimodal, efficiency, open-source weights), summarizes them, and delivers a daily digest through a high-performance static website and an optional Telegram message.

---

## 📑 Table of Contents
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Configuration](#configuration)
- [Run Profiles](#run-profiles)
- [Testing](#testing)
- [Security & Ethics](#security--ethics)

---

## 🏗️ Architecture

```
            ┌────────────────────────────────────────┐
            │  config/sources.yaml  config/topics.yaml│
            └───────────────┬────────────────────────┘
                            ▼
 [Scheduler: GitHub Actions / cron / local CLI]
                            ▼
 1. FETCH      (polite_http: robots.txt cache, rate limit 3s, ETag, allowlist)
                            ▼
 2. NORMALIZE  (title, authors, org, date, url, abstract, source_type)
                            ▼
 3. DEDUPE     (exact UID + canonical URL + arXiv ID + RapidFuzz fuzzy title >= 90%)
                            ▼
 4. CLASSIFY   (topic tags: RAG, LLM, MCP, agents, eval, safety...; org tag)
                            ▼
 5. SCORE      (recency decay + source authority + topic match + trending)
                            ▼
 6. SUMMARIZE  (3 factual bullets + "why it matters", untrusted-data guarded)
                            ▼
 7. STORE      (SQLite + FTS5 full-text search, local bookmarks)
                            ▼
 8. PUBLISH    → Static Website (Jinja2)      → Telegram/Email Daily Digest
```

---

## 🌟 Key Features

1. **Ethical & Polite Aggregation**:
   - Fetches and parses `robots.txt` automatically, cached for 24 hours. Disallowed paths are strictly skipped.
   - Strictly rate-limited to 1 request every 3 seconds per domain.
   - Transparent User-Agent with contact email: `PaperRadar/1.0 (personal research; contact: you@example.com)`.
   - Conditional requests using `ETag` and `If-Modified-Since` (HTTP 304).
   - Circuit-breaker automatically halts sources returning repeated HTTP 403 Forbidden.
2. **Robust Multi-Level Deduplication**:
   - Exact UID and canonical URL matching (tracking query parameters stripped).
   - arXiv ID normalization.
   - RapidFuzz token-based title similarity matching (>= 90% threshold).
3. **Keyword-Based Topic Classification**:
   - Real-time tagging across: `rag`, `llm`, `agents`, `mcp`, `eval`, `safety`, `multimodal`, `efficiency`, `opensource`, `policy`, `okf`.
4. **Weighted Composite Scoring**:
   - `Score = 0.35 × Recency + 0.25 × Authority + 0.25 × Topic Match + 0.15 × Trending`
   - Recency decays exponentially with a 72-hour half-life.
   - Authority tiered across frontier labs (DeepMind, OpenAI, Anthropic, Meta AI) and top institutions (MIT, Stanford, Berkeley).
5. **Prompt-Injection Guarded Summarization**:
   - Default extractive mode generates 3 factual bullets and a "Why it matters" impact sentence.
   - Scraped text is sanitized and defanged; malicious prompt injections (`"ignore previous instructions"`) are defused.
6. **Ultra-Modern Static Web App**:
   - Glassmorphic, dark/light theme, responsive cards, zero external scripts or tracking cookies.
   - Client-side instant full-text search across all indexed items.
   - Client-side bookmarks stored in local storage for privacy.
   - Native RSS feed output (`feed.xml`).

---

## 📂 Repository Structure

```
paper-radar/
├── README.md                 # Project guide and overview
├── SOURCES.md                # Verified sources, retrieval methods, and terms links
├── SECURITY.md               # Security, ethical crawling, and data policies
├── pyproject.toml            # Project build configuration and pytest setup
├── requirements.txt          # Python dependencies
├── .env.example              # Example environment variables
├── .gitignore                # Excludes DB, .env, and build artifacts
├── config/
│   ├── settings.yaml         # Run profile, rate limits, timeouts, scoring weights
│   ├── topics.yaml           # Keyword taxonomy for automated tagging
│   └── sources.yaml          # Verified feed URLs, domains, and authority tiers
├── radar/
│   ├── __init__.py
│   ├── __main__.py           # Entry point for python -m radar
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Config loader with environment overrides
│   ├── polite_http.py        # Robots.txt, rate limiter, ETag, allowlist client
│   ├── normalize.py          # Data schema and text/URL sanitation
│   ├── dedupe.py             # Exact identifier and fuzzy title deduplication
│   ├── classify.py           # Topic tagging and organization detection
│   ├── score.py              # Composite scoring with exponential decay
│   ├── summarize.py          # Extractive summarizer with prompt injection defense
│   ├── store.py              # SQLite + FTS5 full-text search and bookmarks
│   ├── publish_site.py       # Jinja2 static site and RSS feed generator
│   ├── notify.py             # Telegram daily digest notifications
│   ├── pipeline.py           # Full end-to-end orchestrator
│   └── fetchers/             # Dedicated fetchers for arXiv, RSS, HF, GitHub
├── templates/                # Jinja2 HTML templates (autoescaping on)
├── site/                     # Generated static website output
├── tests/                    # Pytest test suite with offline fixtures
└── .github/workflows/
    ├── daily.yml             # Scheduled daily cron run & deploy to GitHub Pages
    └── security.yml          # Pip-audit and Bandit static analysis
```

---

## 🚀 Quick Start

### 1. Clone & Setup Environment
```bash
git clone https://github.com/your-username/paper-radar.git
cd paper-radar

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Edit `.env` to set your contact email (required for ethical scraping User-Agent headers) and optional Telegram credentials:
```ini
RADAR_CONTACT_EMAIL=your.email@example.com
RADAR_PROFILE=LOCAL_LITE
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

### 3. Run the Full Pipeline
```bash
python -m radar run
```

### 4. Serve the Website Locally
```bash
python -m http.server -d site 8000
```
Open **`http://localhost:8000`** in your browser.

---

## 🛠️ CLI Reference

The `radar` CLI provides convenient subcommands:

| Command | Description | Example |
|---|---|---|
| `python -m radar run` | Run full pipeline (fetch, score, summarize, build site) | `python -m radar run --profile LOCAL_LITE` |
| `python -m radar fetch` | Fetch and index items without rebuilding the site | `python -m radar fetch --limit 50` |
| `python -m radar build` | Re-render static HTML site and search index from SQLite | `python -m radar build` |
| `python -m radar search` | Query items using SQLite FTS5 full-text search | `python -m radar search "RAG chunking"` |
| `python -m radar stats` | Display database metrics and topic breakdown | `python -m radar stats` |
| `python -m radar notify` | Print or send Telegram daily digest of top 10 items | `python -m radar notify` |
| `python -m radar bookmark` | Save a paper to private local bookmarks table | `python -m radar bookmark 1 --note "Review for project"` |
| `python -m radar bookmarks`| List private bookmarks and notes | `python -m radar bookmarks` |

---

## ⚙️ Configuration

### `config/settings.yaml`
Control global parameters, rate limits, scoring weights, and summary modes:
```yaml
profile: LOCAL_LITE
request_interval_seconds: 3.0
timeout_seconds: 15
max_response_bytes: 2000000
scoring:
  recency_weight: 0.35
  authority_weight: 0.25
  topic_weight: 0.25
  trending_weight: 0.15
  decay_half_life_hours: 72
```

### `config/topics.yaml`
Add or customize keyword triggers for domain tags:
```yaml
topics:
  rag: [retrieval-augmented, rag, retriever, reranker, vector database, graphrag]
  mcp: [model context protocol, mcp, tool protocol]
```

### `config/sources.yaml`
Register verified RSS feeds, arXiv queries, and GitHub releases. Each source includes a domain allowlist entry and an authority tier.

---

## 🧪 Testing

The test suite contains 20 comprehensive unit and integration tests using offline fixtures:
```bash
pytest
```
Tests cover:
- URL allowlist and HTTPS enforcement
- `robots.txt` parsing and circuit breaker (3 consecutive 403s)
- Deduplication (exact UID, URL, arXiv ID, fuzzy title similarity)
- Keyword topic classification and organization inference
- Exponential recency decay and composite scoring
- Extractive summarization and prompt-injection defense
- SQLite CRUD, triggers, and FTS5 full-text search
- Offline fixture parsing for arXiv XML, RSS feeds, Hugging Face JSON, and GitHub releases
- End-to-end pipeline execution and static site generation

---

## 🔒 Security & Ethics

- See [SECURITY.md](SECURITY.md) for full security disclosures and architecture guarantees.
- See [SOURCES.md](SOURCES.md) for a comprehensive list of indexed publishers and terms of use.
