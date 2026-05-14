"""Safe, testable HTTP fetching for XSMB result pages."""

from __future__ import annotations

import time

import requests

from xsmb.scraping.sources import XSMBSourceConfig


class FetchError(RuntimeError):
    """Raised when an XSMB page cannot be fetched safely."""


def fetch_url(url: str, source_config: XSMBSourceConfig) -> str:
    """Fetch a URL with timeout, user-agent, retry, and clear errors."""
    if source_config.max_attempts <= 0:
        raise ValueError("source_config.max_attempts must be positive")

    last_error: Exception | None = None
    headers = {"User-Agent": source_config.user_agent}

    for attempt in range(1, source_config.max_attempts + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=source_config.timeout_seconds,
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            last_error = exc
            if attempt < source_config.max_attempts:
                time.sleep(source_config.backoff_seconds)

    raise FetchError(
        f"Failed to fetch {url!r} from {source_config.source_name!r} "
        f"after {source_config.max_attempts} attempts"
    ) from last_error
