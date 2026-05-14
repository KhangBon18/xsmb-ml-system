"""Scraping utilities for XSMB result pages."""

from xsmb.scraping.crawler import FetchError, fetch_url
from xsmb.scraping.ingest import IngestionResult, ingest_xsmb_html
from xsmb.scraping.parser import ParseError, parse_xsmb_result_html
from xsmb.scraping.sources import (
    XSMBSourceConfig,
    build_result_url,
    get_default_xsmb_source,
)

__all__ = [
    "FetchError",
    "IngestionResult",
    "ParseError",
    "XSMBSourceConfig",
    "build_result_url",
    "fetch_url",
    "get_default_xsmb_source",
    "ingest_xsmb_html",
    "parse_xsmb_result_html",
]
