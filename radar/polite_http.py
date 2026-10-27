"""Polite HTTP Client with robots.txt enforcement, rate limiting, and security constraints."""

from __future__ import annotations

import logging
import time
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import httpx

from radar.config import RadarConfig, get_config

logger = logging.getLogger("radar.polite_http")


class PoliteHttpClient:
    """An ethical, robust HTTP client adhering to robots.txt, rate limits, and size caps."""

    def __init__(self, config: Optional[RadarConfig] = None):
        self.config = config or get_config()
        self.domain_last_request: Dict[str, float] = {}
        self.domain_consecutive_403: Dict[str, int] = {}
        self.robots_cache: Dict[str, Tuple[RobotFileParser, float]] = {}  # domain -> (parser, expiry_time)
        self.robots_ttl_seconds = 24 * 3600  # 24 hours

    def _get_domain(self, url: str) -> str:
        """Extracts lowercased hostname from a URL."""
        parsed = urlparse(url)
        return (parsed.hostname or "").lower()

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """Validates that a URL is HTTPS and belongs to an allowlisted domain."""
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https":
            return False, f"URL scheme must be HTTPS, got '{parsed.scheme}' for {url}"

        domain = (parsed.hostname or "").lower()
        if not domain:
            return False, f"Missing domain in URL: {url}"

        allowlist = self.config.allowlisted_domains
        # Allow exact match or subdomain match
        allowed = any(domain == d or domain.endswith("." + d) for d in allowlist)
        if not allowed:
            return False, f"Domain '{domain}' is not in the allowlist ({allowlist})"

        return True, ""

    def _wait_for_rate_limit(self, domain: str) -> None:
        """Enforces a strict rate limit per domain (e.g. 1 request per 3 seconds)."""
        now = time.time()
        last_req = self.domain_last_request.get(domain, 0.0)
        elapsed = now - last_req
        needed = self.config.request_interval_seconds

        if elapsed < needed:
            sleep_time = needed - elapsed
            logger.debug(f"Rate limiting {domain}: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.domain_last_request[domain] = time.time()

    def get_robot_parser(self, domain: str) -> RobotFileParser:
        """Fetches and caches robots.txt for a domain for 24 hours."""
        now = time.time()
        if domain in self.robots_cache:
            parser, expiry = self.robots_cache[domain]
            if now < expiry:
                return parser

        rp = RobotFileParser()
        robots_url = f"https://{domain}/robots.txt"

        try:
            self._wait_for_rate_limit(domain)
            headers = {"User-Agent": self.config.user_agent}
            with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                resp = client.get(robots_url, headers=headers)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                    logger.debug(f"Fetched and parsed robots.txt for {domain}")
                elif resp.status_code in (401, 403):
                    # If robots.txt itself is 403, disallow all
                    rp.disallow_all = True
                    logger.warning(f"robots.txt for {domain} returned {resp.status_code}; disallowing")
                else:
                    # 404 or other status code means no restrictions specified
                    rp.allow_all = True
        except Exception as e:
            logger.debug(f"Could not fetch robots.txt for {domain} ({e}); defaulting to allow")
            rp.allow_all = True

        self.robots_cache[domain] = (rp, now + self.robots_ttl_seconds)
        return rp

    def is_allowed_by_robots(self, url: str) -> bool:
        """Checks if URL path is allowed by robots.txt."""
        domain = self._get_domain(url)
        if not domain:
            return False

        rp = self.get_robot_parser(domain)
        # Check for specific user agent or wildcard '*'
        allowed = rp.can_fetch(self.config.user_agent, url) or rp.can_fetch("*", url)
        return allowed

    def get(
        self,
        url: str,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
        max_retries: int = 3,
        is_api: bool = False,
    ) -> Tuple[Optional[httpx.Response], str]:
        """Performs an ethical, safe GET request with retries, size cap, and robots obedience.

        Returns:
            Tuple of (response or None, error_message or reason)
        """
        valid, reason = self.validate_url(url)
        if not valid:
            logger.warning(f"Validation failed for {url}: {reason}")
            return None, reason

        domain = self._get_domain(url)

        # Stop source if repeated 403s
        consecutive_403 = self.domain_consecutive_403.get(domain, 0)
        if consecutive_403 >= 3:
            msg = f"Skipping {domain}: disabled due to {consecutive_403} consecutive 403 errors"
            logger.warning(msg)
            return None, msg

        # Obey robots.txt for web scraping (official APIs follow their documented API terms)
        if not is_api and not self.is_allowed_by_robots(url):
            msg = f"URL disallowed by robots.txt: {url}"
            logger.warning(msg)
            return None, msg

        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, application/json, text/xml;q=0.9, text/html;q=0.8, */*;q=0.5",
        }
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified

        attempt = 0
        backoff = 2.0

        while attempt < max_retries:
            attempt += 1
            self._wait_for_rate_limit(domain)

            try:
                # Custom redirect handler to prevent SSRF or redirect to non-allowlisted hosts
                with httpx.Client(
                    timeout=self.config.timeout_seconds,
                    follow_redirects=False,
                ) as client:
                    current_url = url
                    redirect_count = 0

                    while redirect_count < 5:
                        req_headers = dict(headers)
                        resp = client.get(current_url, headers=req_headers)

                        # Handle redirect safely
                        if resp.is_redirect:
                            redirect_count += 1
                            next_url = resp.headers.get("location")
                            if not next_url:
                                return None, "Redirect location header missing"

                            # Resolve relative redirect if needed
                            if not next_url.startswith("http"):
                                next_url = str(httpx.URL(current_url).join(next_url))

                            valid, reason = self.validate_url(next_url)
                            if not valid:
                                return None, f"Redirect to non-allowlisted host rejected: {next_url} ({reason})"

                            current_url = next_url
                            domain = self._get_domain(current_url)
                            continue

                        # Check size limit
                        content_length = resp.headers.get("content-length")
                        if content_length and int(content_length) > self.config.max_response_bytes:
                            return None, f"Content-Length {content_length} exceeds max allowed {self.config.max_response_bytes} bytes"

                        if len(resp.content) > self.config.max_response_bytes:
                            return None, f"Response body size ({len(resp.content)}) exceeds max {self.config.max_response_bytes} bytes"

                        # Check status
                        if resp.status_code == 304:
                            logger.info(f"304 Not Modified: {url}")
                            return resp, "not_modified"

                        if resp.status_code == 403:
                            self.domain_consecutive_403[domain] = consecutive_403 + 1
                            return resp, f"HTTP 403 Forbidden on {url}"

                        if resp.status_code in (429, 500, 502, 503, 504):
                            logger.warning(f"HTTP {resp.status_code} on {url}, backing off {backoff:.1f}s")
                            time.sleep(backoff)
                            backoff *= 2.0
                            continue

                        # Reset 403 counter on success
                        self.domain_consecutive_403[domain] = 0
                        return resp, "ok"

            except httpx.TimeoutException:
                logger.warning(f"Timeout on {url} (attempt {attempt}/{max_retries})")
                time.sleep(backoff)
                backoff *= 2.0
            except httpx.RequestError as e:
                logger.warning(f"Request error on {url}: {e} (attempt {attempt}/{max_retries})")
                time.sleep(backoff)
                backoff *= 2.0

        return None, f"Max retries ({max_retries}) exceeded for {url}"
