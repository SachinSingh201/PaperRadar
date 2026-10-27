"""Tests for offline fixture-based parsing across all fetcher formats."""

import json
from radar.fetchers.arxiv import parse_arxiv_xml
from radar.fetchers.github_releases import parse_github_atom
from radar.fetchers.huggingface import parse_hf_papers_json
from radar.fetchers.rss import parse_rss_content


def test_arxiv_fixture_parser(fixtures_dir):
    xml_data = (fixtures_dir / "arxiv_sample.xml").read_text(encoding="utf-8")
    items = parse_arxiv_xml(xml_data, source_id="arxiv-cs-ai")

    assert len(items) == 1
    item = items[0]
    assert "GraphRAG" in item.title
    assert "Alice Johnson" in item.authors
    assert item.uid == "arxiv:2501.01234"
    assert item.source_type == "paper"
    assert "hierarchical knowledge graphs" in item.abstract.lower()


def test_rss_fixture_parser(fixtures_dir):
    rss_data = (fixtures_dir / "rss_sample.xml").read_text(encoding="utf-8")
    source_info = {"id": "deepmind-blog", "org": "Google DeepMind", "type": "blog"}
    items = parse_rss_content(rss_data, source_info)

    assert len(items) == 1
    item = items[0]
    assert "Gemini 2.0" in item.title
    assert item.org == "Google DeepMind"
    assert item.source_type == "blog"
    assert "multimodal" in item.abstract.lower()


def test_huggingface_fixture_parser(fixtures_dir):
    json_data = json.loads((fixtures_dir / "hf_daily_papers.json").read_text(encoding="utf-8"))
    source_info = {"id": "hf-papers", "org": "Hugging Face", "type": "paper"}
    items = parse_hf_papers_json(json_data, source_info)

    assert len(items) == 1
    item = items[0]
    assert "DeepSeek-V3" in item.title
    assert item.uid == "arxiv:2412.19437"
    assert item.extra_metadata.get("upvotes") == 340


def test_github_releases_fixture_parser(fixtures_dir):
    atom_data = (fixtures_dir / "github_releases.atom").read_text(encoding="utf-8")
    source_info = {"id": "mcp-spec", "name": "MCP Specification", "org": "Anthropic", "type": "spec"}
    items = parse_github_atom(atom_data, source_info)

    assert len(items) == 1
    item = items[0]
    assert "v1.0.0" in item.title
    assert item.source_type == "spec"
    assert "Model Context Protocol" in item.abstract
