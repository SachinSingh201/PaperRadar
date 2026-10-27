"""Tests for Deduplicator: UID, URL, and fuzzy title matching."""

from radar.dedupe import Deduplicator
from radar.normalize import RadarItem


def test_exact_uid_dedupe():
    deduper = Deduplicator()
    item1 = RadarItem(uid="arxiv:2501.0001", title="Title A", url="https://arxiv.org/abs/2501.0001", source="arxiv")
    item2 = RadarItem(uid="arxiv:2501.0001", title="Different Title", url="https://arxiv.org/abs/2501.0001", source="arxiv")

    batch = [item1, item2]
    unique = deduper.filter_batch(batch)
    assert len(unique) == 1
    assert unique[0].uid == "arxiv:2501.0001"


def test_normalized_url_dedupe():
    deduper = Deduplicator()
    item1 = RadarItem(uid="url:12345", title="Paper One", url="https://example.com/post?utm_source=twitter&ref=ai", source="rss")
    item2 = RadarItem(uid="url:67890", title="Paper One", url="https://example.com/post?utm_medium=email", source="rss")

    deduper.register_existing([item1])
    is_dup, reason = deduper.is_duplicate(item2)
    assert is_dup
    assert "exact_url" in reason


def test_fuzzy_title_dedupe():
    deduper = Deduplicator(fuzzy_threshold=88.0)
    item1 = RadarItem(
        uid="arxiv:2401.0001",
        title="Scaling Laws for Precision in Large Language Models",
        url="https://arxiv.org/abs/2401.0001",
        source="arxiv",
    )
    item2 = RadarItem(
        uid="hf:2401.0001",
        title="[Paper] Scaling Laws for Precision in Large Language Model Architectures",
        url="https://huggingface.co/papers/2401.0001",
        source="huggingface",
    )

    deduper.register_existing([item1])
    is_dup, reason = deduper.is_duplicate(item2)
    assert is_dup
    assert "fuzzy_title" in reason or "arxiv_id" in reason
