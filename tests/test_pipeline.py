"""End-to-end pipeline integration test using mock config and fixtures."""

import json
from radar.fetchers.arxiv import parse_arxiv_xml
from radar.fetchers.rss import parse_rss_content
from radar.pipeline import Pipeline


def test_pipeline_processing_and_site_build(mock_config, fixtures_dir):
    pipeline = Pipeline(config=mock_config)

    # 1. Load mock items from fixtures
    arxiv_xml = (fixtures_dir / "arxiv_sample.xml").read_text(encoding="utf-8")
    rss_xml = (fixtures_dir / "rss_sample.xml").read_text(encoding="utf-8")

    items_arxiv = parse_arxiv_xml(arxiv_xml, source_id="arxiv-cs-ai")
    items_rss = parse_rss_content(rss_xml, {"id": "deepmind-blog", "org": "Google DeepMind", "type": "blog"})

    raw_items = items_arxiv + items_rss
    assert len(raw_items) == 2

    # 2. Process items (dedupe, classify, score, summarize)
    processed = pipeline.process_items(raw_items)
    assert len(processed) == 2

    # Verify classification, scoring and summarization
    for it in processed:
        assert it.topics != ""
        assert it.score > 0.0
        assert "- " in it.summary
        assert "**Why it matters:**" in it.summary

    # 3. Insert into SQLite
    inserted = pipeline.storage.insert_items(processed)
    assert inserted == 2

    # 4. Build static website
    pipeline.publisher.build()

    site_dir = mock_config.site_dir
    assert (site_dir / "index.html").exists()
    assert (site_dir / "week.html").exists()
    assert (site_dir / "topics.html").exists()
    assert (site_dir / "organizations.html").exists()
    assert (site_dir / "search.html").exists()
    assert (site_dir / "about.html").exists()
    assert (site_dir / "feed.xml").exists()
    assert (site_dir / "search_index.json").exists()
    assert (site_dir / "style.css").exists()
    assert (site_dir / "app.js").exists()

    # Verify search index json content
    search_records = json.loads((site_dir / "search_index.json").read_text(encoding="utf-8"))
    assert len(search_records) == 2
