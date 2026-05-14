"""HTML parser for XSMB result pages."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from bs4 import BeautifulSoup

from xsmb.config import PRIZE_SPECS, PRIZE_TIERS
from xsmb.processing.normalize import normalize_number
from xsmb.processing.validate import validate_draw_results


class ParseError(ValueError):
    """Raised when an XSMB result page cannot be parsed into a valid draw."""


TIER_ALIASES: dict[str, tuple[str, ...]] = {
    "special": ("special", "gdb", "db", "dac-biet", "dac_biet"),
    "first": ("first", "g1", "nhat"),
    "second": ("second", "g2", "nhi"),
    "third": ("third", "g3", "ba"),
    "fourth": ("fourth", "g4", "tu"),
    "fifth": ("fifth", "g5", "nam"),
    "sixth": ("sixth", "g6", "sau"),
    "seventh": ("seventh", "g7", "bay"),
}


def parse_xsmb_result_html(html: str, draw_date: str | date) -> list[dict[str, Any]]:
    """Parse static XSMB result HTML into normalized zero-based prize rows."""
    if not isinstance(html, str) or html.strip() == "":
        raise ParseError("HTML input is empty")

    draw_date_str = _coerce_draw_date(draw_date)
    soup = BeautifulSoup(html, "html.parser")
    root = _find_result_root(soup)
    rows: list[dict[str, Any]] = []

    for prize_tier in PRIZE_TIERS:
        container = _find_tier_container(root, prize_tier)
        raw_numbers = _extract_numbers_from_container(container)
        expected_count = PRIZE_SPECS[prize_tier]["count"]
        expected_length = PRIZE_SPECS[prize_tier]["length"]

        if len(raw_numbers) != expected_count:
            raise ParseError(
                f"Prize tier {prize_tier!r} must contain {expected_count} numbers, "
                f"got {len(raw_numbers)}"
            )

        for prize_index, raw_number in enumerate(raw_numbers):
            try:
                winning_number = normalize_number(raw_number, expected_length)
            except (TypeError, ValueError) as exc:
                raise ParseError(
                    f"Invalid number for {prize_tier}[{prize_index}]: {raw_number!r}"
                ) from exc
            rows.append(
                {
                    "draw_date": draw_date_str,
                    "prize_tier": prize_tier,
                    "prize_index": prize_index,
                    "winning_number": winning_number,
                }
            )

    try:
        validate_draw_results(rows)
    except (TypeError, ValueError) as exc:
        raise ParseError(f"Parsed XSMB result is invalid: {exc}") from exc
    return rows


def _coerce_draw_date(value: str | date) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return date.fromisoformat(value).isoformat()
    raise TypeError(f"draw_date must be str or date, got {type(value).__name__}")


def _find_result_root(soup: BeautifulSoup):
    root = soup.find(attrs={"data-xsmb-result": True})
    if root is not None:
        return root

    root = soup.find(id=re.compile(r"(xsmb|result|ket-qua)", re.IGNORECASE))
    if root is not None:
        return root

    return soup


def _find_tier_container(root, prize_tier: str):
    aliases = TIER_ALIASES[prize_tier]
    candidates = []

    for attr_name in ("data-prize-tier", "data-tier"):
        candidates.extend(
            tag
            for tag in root.find_all(attrs={attr_name: True})
            if _normalize_token(tag.get(attr_name)) in aliases
        )

    if not candidates:
        candidates.extend(
            tag
            for tag in root.find_all(class_=True)
            if _classes_match_alias(tag.get("class", []), aliases)
        )

    unique_candidates = []
    seen_ids = set()
    for candidate in candidates:
        candidate_id = id(candidate)
        if candidate_id not in seen_ids:
            unique_candidates.append(candidate)
            seen_ids.add(candidate_id)

    if len(unique_candidates) == 0:
        raise ParseError(f"Cannot find expected XSMB section for {prize_tier!r}")
    if len(unique_candidates) > 1:
        raise ParseError(f"Duplicate/malformed sections for {prize_tier!r}")
    return unique_candidates[0]


def _extract_numbers_from_container(container) -> list[str]:
    number_tags = container.find_all(attrs={"data-winning-number": True})
    if number_tags:
        return [_clean_number(tag.get("data-winning-number", "")) for tag in number_tags]

    number_tags = container.find_all(
        class_=lambda value: value
        and any(token in str(value).lower() for token in ("winning-number", "prize-number"))
    )
    if number_tags:
        return [_clean_number(tag.get_text("", strip=True)) for tag in number_tags]

    text = container.get_text(" ", strip=True)
    return [_clean_number(match) for match in re.findall(r"\b\d{2,5}\b", text)]


def _clean_number(value: str) -> str:
    return re.sub(r"\s+", "", value.strip())


def _normalize_token(value: object) -> str:
    return str(value).strip().lower().replace(" ", "-").replace("_", "-")


def _classes_match_alias(classes: object, aliases: tuple[str, ...]) -> bool:
    if isinstance(classes, str):
        class_values = classes.split()
    else:
        class_values = [str(class_name) for class_name in classes]

    normalized_aliases = {_normalize_token(alias) for alias in aliases}
    for class_name in class_values:
        normalized_class = _normalize_token(class_name)
        if normalized_class in normalized_aliases:
            return True
        if normalized_class.startswith("prize-") and normalized_class[6:] in normalized_aliases:
            return True
    return False
