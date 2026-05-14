"""Tests for safe XSMB HTTP fetching."""

from __future__ import annotations

import pytest
import requests

from xsmb.scraping.crawler import FetchError, fetch_url
from xsmb.scraping.sources import (
    XSMBSourceConfig,
    build_result_url,
    get_default_xsmb_source,
)


class FakeResponse:
    """Minimal fake requests response for crawler tests."""

    def __init__(self, text: str = "ok", error: Exception | None = None) -> None:
        self.text = text
        self.error = error

    def raise_for_status(self) -> None:
        if self.error is not None:
            raise self.error


def test_build_result_url_formats_single_draw_date() -> None:
    source = get_default_xsmb_source()

    assert build_result_url(source, "2024-01-15").endswith("xsmb-15-01-2024.html")


def test_fetch_url_uses_timeout_and_user_agent(monkeypatch) -> None:
    source = XSMBSourceConfig(
        source_name="unit",
        url_template="https://example.test/{date}",
        timeout_seconds=3.5,
        user_agent="unit-agent",
        parser_version="v1",
    )
    calls = []

    def fake_get(url, headers, timeout):
        calls.append({"url": url, "headers": headers, "timeout": timeout})
        return FakeResponse("html")

    monkeypatch.setattr(requests, "get", fake_get)

    assert fetch_url("https://example.test/page", source) == "html"
    assert calls == [
        {
            "url": "https://example.test/page",
            "headers": {"User-Agent": "unit-agent"},
            "timeout": 3.5,
        }
    ]


def test_fetch_url_retries_then_succeeds(monkeypatch) -> None:
    source = XSMBSourceConfig(
        source_name="unit",
        url_template="https://example.test/{date}",
        timeout_seconds=1.0,
        user_agent="unit-agent",
        parser_version="v1",
        max_attempts=2,
        backoff_seconds=0.01,
    )
    responses = [
        requests.Timeout("timeout"),
        FakeResponse("html"),
    ]
    sleep_calls = []

    def fake_get(url, headers, timeout):
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr("xsmb.scraping.crawler.time.sleep", sleep_calls.append)

    assert fetch_url("https://example.test/page", source) == "html"
    assert sleep_calls == [0.01]


def test_fetch_url_raises_clear_error_after_failures(monkeypatch) -> None:
    source = XSMBSourceConfig(
        source_name="unit",
        url_template="https://example.test/{date}",
        timeout_seconds=1.0,
        user_agent="unit-agent",
        parser_version="v1",
        max_attempts=2,
        backoff_seconds=0.01,
    )

    def fake_get(url, headers, timeout):
        raise requests.ConnectionError("offline")

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr("xsmb.scraping.crawler.time.sleep", lambda seconds: None)

    with pytest.raises(FetchError, match="Failed to fetch"):
        fetch_url("https://example.test/page", source)
