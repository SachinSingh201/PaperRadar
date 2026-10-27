"""Pytest configuration and shared fixtures for Paper Radar."""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from radar.config import RadarConfig
from radar.normalize import RadarItem

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test_radar.db"


@pytest.fixture
def mock_config(tmp_path: Path) -> RadarConfig:
    config = RadarConfig(profile_override="LOCAL_LITE")
    config.db_path = tmp_path / "test_radar.db"
    config.site_dir = tmp_path / "test_site"
    config.request_interval_seconds = 0.01  # fast tests
    return config


@pytest.fixture
def sample_item() -> RadarItem:
    return RadarItem(
        uid="arxiv:2501.01234",
        title="GraphRAG: Unifying Knowledge Graphs and Retrieval-Augmented Generation",
        url="https://arxiv.org/abs/2501.01234",
        source="arxiv-cs-ai",
        source_type="paper",
        authors="Alice Johnson, Bob Smith",
        org="arXiv",
        published_at="2025-01-14T18:00:00Z",
        fetched_at="2025-01-15T00:00:00Z",
        abstract="Retrieval-Augmented Generation (RAG) significantly improves LLM accuracy. We propose GraphRAG, a framework combining hierarchical knowledge graphs with vector retrieval. It outperforms baseline retrievers by 28%.",
        summary="- We propose GraphRAG for complex retrieval.\n- Integrates knowledge graphs with dense retrievers.\n- Outperforms baseline models by 28%.\n\n**Why it matters:** Solves multi-hop reasoning limitations in standard RAG architectures.",
        summary_model="extractive-v1",
        topics="rag,llm",
        score=0.88,
    )
