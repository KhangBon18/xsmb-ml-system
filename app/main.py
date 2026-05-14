"""CLI entry point for the XSMB ML System.

Usage examples:
    python -m app.main scrape --start-date 2024-01-01 --end-date 2024-01-31
    python -m app.main process --start-date 2024-01-01 --end-date 2024-01-31
    python -m app.main build-features --target-type loto_2d_all_prizes
    python -m app.main backtest --target-type loto_2d_all_prizes --model frequency_30
    python -m app.main train --target-type loto_2d_all_prizes --model logistic_regression
    python -m app.main predict --target-date 2024-02-01 --target-type db_3cang --top-k 20
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from xsmb.config import TARGET_TYPES
from xsmb.models.baseline import SUPPORTED_BASELINES
from xsmb.models.train import SUPPORTED_ML_MODELS

ALL_MODEL_NAMES: set[str] = SUPPORTED_BASELINES | SUPPORTED_ML_MODELS

_DESCRIPTION = (
    "XSMB ML System — statistical probability ranking for XSMB 2-digit loto numbers.\n"
    "This tool provides data collection, feature engineering, backtesting, and\n"
    "prediction commands.  It does NOT guarantee winning numbers."
)


# ---------------------------------------------------------------------------
# Argument builder
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="xsmb-ml",
        description=_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    _add_scrape_parser(subparsers)
    _add_process_parser(subparsers)
    _add_build_features_parser(subparsers)
    _add_backtest_parser(subparsers)
    _add_train_parser(subparsers)
    _add_predict_parser(subparsers)

    return parser


# -- Subcommand builders ----------------------------------------------------

def _add_scrape_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("scrape", help="Scrape XSMB results for a date range")
    parser.add_argument(
        "--start-date", required=True,
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end-date", required=True,
        help="End date in YYYY-MM-DD format",
    )


def _add_process_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("process", help="Process and normalize scraped results")
    parser.add_argument(
        "--start-date", required=True,
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end-date", required=True,
        help="End date in YYYY-MM-DD format",
    )


def _add_build_features_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build-features", help="Build leakage-safe feature dataset",
    )
    parser.add_argument(
        "--target-type", required=True, choices=TARGET_TYPES,
        help="Target type to build features for",
    )


def _add_backtest_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "backtest", help="Run walk-forward backtest for a baseline model",
    )
    parser.add_argument(
        "--target-type", required=True, choices=TARGET_TYPES,
        help="Target type to backtest",
    )
    parser.add_argument(
        "--model", required=True, choices=sorted(SUPPORTED_BASELINES),
        help="Baseline model name",
    )


def _add_train_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "train", help="Train an ML model on the feature dataset",
    )
    parser.add_argument(
        "--target-type", required=True, choices=TARGET_TYPES,
        help="Target type to train on",
    )
    parser.add_argument(
        "--model", required=True, choices=sorted(SUPPORTED_ML_MODELS),
        help="ML model name",
    )


def _add_predict_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "predict", help="Generate probability-ranked predictions",
    )
    parser.add_argument(
        "--target-date", required=True,
        help="Date to predict in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--target-type", required=True, choices=TARGET_TYPES,
        help="Target type to predict",
    )
    parser.add_argument(
        "--top-k", type=int, default=20,
        help="Number of top candidates to return (default: 20)",
    )


# ---------------------------------------------------------------------------
# Argument validation helpers
# ---------------------------------------------------------------------------

def _validate_date(date_string: str, label: str) -> str:
    """Validate YYYY-MM-DD format and return the canonical string."""
    import re
    pattern = r"^\d{4}-\d{2}-\d{2}$"
    if not re.match(pattern, date_string):
        raise SystemExit(f"Error: {label} must be YYYY-MM-DD, got: {date_string!r}")
    # Extra validation: ensure it's a real calendar date.
    from datetime import date as _date
    try:
        _date.fromisoformat(date_string)
    except ValueError:
        raise SystemExit(f"Error: {label} is not a valid date: {date_string!r}")
    return date_string


def _validate_top_k(value: int) -> int:
    """Ensure top_k is a positive integer."""
    if value <= 0:
        raise SystemExit(f"Error: --top-k must be a positive integer, got: {value}")
    return value


# ---------------------------------------------------------------------------
# Command handlers (MVP stubs — no network, no real DB)
# ---------------------------------------------------------------------------

def _handle_scrape(args: argparse.Namespace) -> int:
    start = _validate_date(args.start_date, "--start-date")
    end = _validate_date(args.end_date, "--end-date")
    print(f"[scrape] Would scrape XSMB results from {start} to {end}.")
    print("[scrape] MVP stub — no network requests made.")
    return 0


def _handle_process(args: argparse.Namespace) -> int:
    start = _validate_date(args.start_date, "--start-date")
    end = _validate_date(args.end_date, "--end-date")
    print(f"[process] Would process results from {start} to {end}.")
    print("[process] MVP stub — no database writes made.")
    return 0


def _handle_build_features(args: argparse.Namespace) -> int:
    target_type: str = args.target_type
    print(f"[build-features] Would build features for target_type={target_type!r}.")
    print("[build-features] MVP stub — no feature dataset written.")
    return 0


def _handle_backtest(args: argparse.Namespace) -> int:
    target_type: str = args.target_type
    model: str = args.model
    print(f"[backtest] Would run walk-forward backtest: target_type={target_type!r}, model={model!r}.")
    print("[backtest] MVP stub — no backtest executed.")
    return 0


def _handle_train(args: argparse.Namespace) -> int:
    target_type: str = args.target_type
    model: str = args.model
    print(f"[train] Would train model: target_type={target_type!r}, model={model!r}.")
    print("[train] MVP stub — no model trained.")
    return 0


def _handle_predict(args: argparse.Namespace) -> int:
    target_date = _validate_date(args.target_date, "--target-date")
    target_type: str = args.target_type
    top_k = _validate_top_k(args.top_k)
    print(
        f"[predict] Would predict: target_date={target_date}, "
        f"target_type={target_type!r}, top_k={top_k}."
    )
    print("[predict] MVP stub — no prediction generated.")
    return 0


_COMMAND_HANDLERS = {
    "scrape": _handle_scrape,
    "process": _handle_process,
    "build-features": _handle_build_features,
    "backtest": _handle_backtest,
    "train": _handle_train,
    "predict": _handle_predict,
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse CLI arguments and dispatch to the appropriate handler.

    Parameters
    ----------
    argv : sequence of str, optional
        Command-line arguments.  Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Exit code (0 = success).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    handler = _COMMAND_HANDLERS.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
