"""Source configuration for safe XSMB result fetching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class XSMBSourceConfig:
    """Configuration for one XSMB result source."""

    source_name: str
    url_template: str
    timeout_seconds: float
    user_agent: str
    parser_version: str
    max_attempts: int = 2
    backoff_seconds: float = 0.25
    base_url: str | None = None


def get_default_xsmb_source() -> XSMBSourceConfig:
    """Return the default safe XSMB source configuration."""
    return XSMBSourceConfig(
        source_name="xoso_com_vn",
        base_url="https://xoso.com.vn",
        url_template="https://xoso.com.vn/xsmb-{dd}-{mm}-{yyyy}.html",
        timeout_seconds=10.0,
        user_agent="xsmb-ml-system/0.1 (statistical research; contact: local)",
        parser_version="xsmb_html_v1",
        max_attempts=2,
        backoff_seconds=0.25,
    )


def build_result_url(source: XSMBSourceConfig, draw_date: str | date) -> str:
    """Build a source URL for a single XSMB draw date."""
    normalized_date = _coerce_date(draw_date)
    return source.url_template.format(
        yyyy=f"{normalized_date.year:04d}",
        mm=f"{normalized_date.month:02d}",
        dd=f"{normalized_date.day:02d}",
        date=normalized_date.isoformat(),
    )


def _coerce_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise TypeError(f"draw_date must be str or date, got {type(value).__name__}")
