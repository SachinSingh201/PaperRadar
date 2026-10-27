"""Tests for Classifier: Topic keyword extraction and organization inference."""

from radar.classify import Classifier
from radar.normalize import RadarItem


def test_topic_classification(mock_config):
    classifier = Classifier(config=mock_config)

    item = RadarItem(
        uid="test:1",
        title="Agentic Workflows with Model Context Protocol and RAG",
        url="https://example.com/test",
        source="rss",
        abstract="We develop autonomous agent architectures leveraging tool use and MCP protocols for dense retrieval-augmented generation.",
    )

    topics, score = classifier.classify_item(item)
    assert "agents" in topics
    assert "mcp" in topics
    assert "rag" in topics
    assert score > 0.4
    assert "agents" in item.topics


def test_inferred_organization(mock_config):
    classifier = Classifier(config=mock_config)

    item = RadarItem(
        uid="test:2",
        title="Novel Reasoning Models",
        url="https://example.com/test2",
        source="rss",
        abstract="Google DeepMind researchers introduce new pretraining paradigms for frontier transformers.",
    )

    classifier.classify_item(item)
    assert item.org == "Google DeepMind"
