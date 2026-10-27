"""Tests for Scorer: Recency decay, authority weights, and composite scoring."""

import datetime
from radar.normalize import RadarItem
from radar.score import Scorer


def test_recency_decay(mock_config):
    scorer = Scorer(config=mock_config)
    now = datetime.datetime.now(datetime.timezone.utc)

    # Published just now
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    recency_now = scorer.calculate_recency(now_iso, now=now)
    assert recency_now >= 0.99

    # Published 72 hours ago (decay half life)
    old_iso = (now - datetime.timedelta(hours=72)).strftime("%Y-%m-%dT%H:%M:%SZ")
    recency_old = scorer.calculate_recency(old_iso, now=now)
    assert 0.35 <= recency_old <= 0.40  # exp(-1) is ~0.367


def test_composite_score(mock_config):
    scorer = Scorer(config=mock_config)
    now = datetime.datetime.now(datetime.timezone.utc)

    item = RadarItem(
        uid="test:score",
        title="Breakthrough Transformer Scaling",
        url="https://example.com/score",
        source="arxiv-cs-ai",
        org="Google DeepMind",
        published_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        extra_metadata={"upvotes": 20},
    )

    final_score = scorer.score_item(item, topic_match_score=0.9, now=now)
    assert 0.70 <= final_score <= 1.0
    assert item.score == final_score
