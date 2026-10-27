"""Tests for PoliteHttpClient: URL validation, robots.txt obedience, and rate limiting."""

from urllib.robotparser import RobotFileParser
from radar.polite_http import PoliteHttpClient


def test_validate_url_https_enforcement(mock_config):
    client = PoliteHttpClient(config=mock_config)

    # Insecure HTTP must fail
    valid, reason = client.validate_url("http://export.arxiv.org/api/query")
    assert not valid
    assert "HTTPS" in reason

    # HTTPS allowlisted domain must pass
    valid, _ = client.validate_url("https://export.arxiv.org/api/query")
    assert valid


def test_validate_url_domain_allowlist(mock_config):
    client = PoliteHttpClient(config=mock_config)

    # Allowlisted domain
    valid, _ = client.validate_url("https://huggingface.co/api/daily_papers")
    assert valid

    # Non-allowlisted domain must be rejected
    valid, reason = client.validate_url("https://malicious-site.example.com/payload")
    assert not valid
    assert "not in the allowlist" in reason


def test_robots_txt_enforcement(mock_config, fixtures_dir):
    client = PoliteHttpClient(config=mock_config)
    rp = RobotFileParser()
    robots_text = (fixtures_dir / "robots.txt").read_text(encoding="utf-8")
    rp.parse(robots_text.splitlines())

    # Cache this parser for example domain
    client.robots_cache["example-allowed.com"] = (rp, 9999999999.0)

    # Allowed path
    assert rp.can_fetch(mock_config.user_agent, "https://example-allowed.com/public/feed.xml")

    # Disallowed paths
    assert not rp.can_fetch(mock_config.user_agent, "https://example-allowed.com/private/secret.html")
    assert not rp.can_fetch(mock_config.user_agent, "https://example-allowed.com/admin/dashboard")


def test_consecutive_403_circuit_breaker(mock_config):
    client = PoliteHttpClient(config=mock_config)
    domain = "export.arxiv.org"

    # Simulate 3 consecutive 403 errors
    client.domain_consecutive_403[domain] = 3

    resp, reason = client.get("https://export.arxiv.org/api/query")
    assert resp is None
    assert "consecutive 403" in reason
