"""Core domain constants for XSMB draw processing."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DATABASE_URL = "sqlite:///data/xsmb.sqlite3"
DATABASE_URL_ENV_VAR = "DATABASE_URL"

PRIZE_SPECS: dict[str, dict[str, int]] = {
    "special": {"count": 1, "length": 5},
    "first": {"count": 1, "length": 5},
    "second": {"count": 2, "length": 5},
    "third": {"count": 6, "length": 5},
    "fourth": {"count": 4, "length": 4},
    "fifth": {"count": 6, "length": 4},
    "sixth": {"count": 3, "length": 3},
    "seventh": {"count": 4, "length": 2},
}

PRIZE_TIERS: tuple[str, ...] = tuple(PRIZE_SPECS)
TOTAL_PRIZE_COUNT = sum(spec["count"] for spec in PRIZE_SPECS.values())

TARGET_LOTO_2D_ALL_PRIZES = "loto_2d_all_prizes"
TARGET_DB_2CANG = "db_2cang"
TARGET_DB_3CANG = "db_3cang"

TARGET_TYPES: tuple[str, ...] = (
    TARGET_LOTO_2D_ALL_PRIZES,
    TARGET_DB_2CANG,
    TARGET_DB_3CANG,
)

LOTO_2D_NUMBERS: list[str] = [f"{number:02d}" for number in range(100)]
DB_3CANG_NUMBERS: list[str] = [f"{number:03d}" for number in range(1000)]
