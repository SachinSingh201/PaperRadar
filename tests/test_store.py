"""Tests for SQLite Storage: Table initialization, insertion, FTS5 search, and bookmarks."""

from radar.normalize import RadarItem
from radar.store import Storage


def test_storage_crud_and_fts(temp_db_path, mock_config, sample_item):
    mock_config.db_path = temp_db_path
    storage = Storage(config=mock_config)

    # Insert item
    inserted = storage.insert_items([sample_item])
    assert inserted == 1

    # Duplicate insert should return 0
    dup_inserted = storage.insert_items([sample_item])
    assert dup_inserted == 0

    # Retrieve all
    all_items = storage.get_all_items()
    assert len(all_items) == 1
    assert all_items[0].title == sample_item.title

    # FTS5 search
    results = storage.search_fts("GraphRAG")
    assert len(results) == 1
    assert results[0].uid == sample_item.uid

    # FTS5 non-matching search
    no_results = storage.search_fts("NonExistentTermXYZ")
    assert len(no_results) == 0


def test_local_bookmarks(temp_db_path, mock_config, sample_item):
    mock_config.db_path = temp_db_path
    storage = Storage(config=mock_config)
    storage.insert_items([sample_item])

    items = storage.get_all_items()
    item_id = items[0].id
    assert item_id is not None

    bm_id = storage.add_bookmark(item_id=item_id, note="Must read for RAG system design")
    assert bm_id > 0

    bookmarks = storage.get_bookmarks()
    assert len(bookmarks) == 1
    assert bookmarks[0]["note"] == "Must read for RAG system design"
    assert bookmarks[0]["title"] == sample_item.title
