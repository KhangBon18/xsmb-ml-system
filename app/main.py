"""CLI entry point for the XSMB ML System.

Usage examples:
    python -m app.main scrape --start-date 2024-01-01 --end-date 2024-01-31
    python -m app.main process --start-date 2024-01-01 --end-date 2024-01-31
    python -m app.main build-features --target-type loto_2d_all_prizes
    python -m app.main backtest --target-type loto_2d_all_prizes --model frequency_30 --history-csv data.csv
    python -m app.main train --target-type loto_2d_all_prizes --model logistic_regression --features-csv feat.csv --artifact-dir tmp/models
    python -m app.main predict --target-date 2024-02-01 --target-type db_3cang --top-k 20 --features-csv feat.csv --artifact model.pkl
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, Sequence

import pandas as pd

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
    parser.add_argument(
        "--history-csv", default=None,
        help="Path to history CSV (columns: draw_date, target_type, candidate_number, label, hit_count)",
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
    parser.add_argument(
        "--features-csv", default=None,
        help="Path to feature dataset CSV",
    )
    parser.add_argument(
        "--artifact-dir", default="data/models",
        help="Directory to save trained model artifact (default: data/models)",
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
    parser.add_argument(
        "--features-csv", default=None,
        help="Path to feature dataset CSV for prediction",
    )
    parser.add_argument(
        "--artifact", default=None,
        help="Path to trained model artifact (.pkl)",
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
# CSV I/O helpers
# ---------------------------------------------------------------------------

_STRING_COLUMNS = {"candidate_number", "draw_date", "target_date", "target_type"}

logger = logging.getLogger(__name__)


def _read_csv_safe(csv_path: str) -> pd.DataFrame:
    """Read a CSV ensuring candidate_number and similar columns stay as strings."""
    path = Path(csv_path)
    if not path.exists():
        raise SystemExit(f"Error: CSV file not found: {csv_path!r}")
    try:
        df = pd.read_csv(path, dtype={col: str for col in _STRING_COLUMNS})
    except Exception as exc:
        raise SystemExit(f"Error: failed to read CSV {csv_path!r}: {exc}") from exc
    # Ensure candidate_number is always string with leading zeros preserved.
    if "candidate_number" in df.columns:
        df["candidate_number"] = df["candidate_number"].astype(str)
    return df


# ---------------------------------------------------------------------------
# Command handlers (MVP stubs + CSV-wired modes)
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

    if args.history_csv is None:
        print(f"[backtest] Would run walk-forward backtest: target_type={target_type!r}, model={model!r}.")
        print("[backtest] MVP stub — no backtest executed.")
        return 0

    from xsmb.models.backtest import run_walk_forward_backtest, summarize_backtest_result

    history_df = _read_csv_safe(args.history_csv)
    result = run_walk_forward_backtest(
        history_df, target_type=target_type, model_name=model,
    )
    summary = summarize_backtest_result(result)
    print(json.dumps(summary, indent=2, default=str))
    return 0


def _handle_train(args: argparse.Namespace) -> int:
    target_type: str = args.target_type
    model: str = args.model

    if args.features_csv is None:
        print(f"[train] Would train model: target_type={target_type!r}, model={model!r}.")
        print("[train] MVP stub — no model trained.")
        return 0

    from xsmb.models.train import save_model_artifact, train_model

    feature_df = _read_csv_safe(args.features_csv)
    trained = train_model(feature_df, target_type=target_type, model_name=model)
    artifact_path = save_model_artifact(trained, artifact_dir=args.artifact_dir)
    output = {
        "artifact_path": artifact_path,
        "model_name": trained["model_name"],
        "target_type": trained["target_type"],
        "row_count": trained["row_count"],
    }
    print(json.dumps(output, indent=2))
    return 0


def _handle_predict(args: argparse.Namespace) -> int:
    target_date = _validate_date(args.target_date, "--target-date")
    target_type: str = args.target_type
    top_k = _validate_top_k(args.top_k)

    features_csv = getattr(args, "features_csv", None)
    artifact_path = getattr(args, "artifact", None)

    if features_csv is None or artifact_path is None:
        print(
            f"[predict] Would predict: target_date={target_date}, "
            f"target_type={target_type!r}, top_k={top_k}."
        )
        print("[predict] MVP stub — no prediction generated.")
        return 0

    from xsmb.models.predict import predict_probabilities
    from xsmb.models.train import load_model_artifact

    if not Path(artifact_path).exists():
        raise SystemExit(f"Error: artifact file not found: {artifact_path!r}")

    trained_model = load_model_artifact(artifact_path)
    feature_df = _read_csv_safe(features_csv)
    predictions = predict_probabilities(
        trained_model,
        feature_df,
        target_date=target_date,
        top_k=top_k,
    )
    # Ensure candidate_number strings are preserved (leading zeros).
    predictions["candidate_number"] = predictions["candidate_number"].astype(str)
    records = predictions.to_dict(orient="records")
    print(json.dumps(records, indent=2, default=str))
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
# API application export (Phase 7C)
# ---------------------------------------------------------------------------

def create_api_app() -> "FastAPI" | None:
    """Create and return the FastAPI application instance."""
    try:
        from fastapi import FastAPI
        from xsmb.api.routes import router as api_router
    except ImportError:
        return None

    if api_router is None:
        return None

    app = FastAPI(
        title="XSMB ML System",
        description=_DESCRIPTION,
        version="0.1.0",
    )
    app.include_router(api_router)
    return app

# Expose an instance for ASGI servers (e.g. uvicorn app.main:api_app)
api_app = create_api_app()


# ---------------------------------------------------------------------------
# CLI Entry point
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
