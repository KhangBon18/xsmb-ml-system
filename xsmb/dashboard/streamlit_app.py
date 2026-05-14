"""Local Streamlit dashboard for XSMB probability-ranking reports.

The pure helper functions in this module are intentionally import-safe and do
not require Streamlit. The UI reads local uploaded files only.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from xsmb.config import TARGET_TYPES

DISCLAIMER = (
    "This dashboard shows probability rankings and statistical backtest results. "
    "It does not guarantee lottery outcomes."
)

REQUIRED_PREDICTION_COLUMNS: tuple[str, ...] = (
    "target_type",
    "candidate_number",
    "probability",
    "rank",
)
PREDICTION_DISPLAY_COLUMNS: tuple[str, ...] = (
    "target_date",
    "target_type",
    "candidate_number",
    "probability",
    "rank",
    "model_name",
)
CALIBRATION_COLUMNS: tuple[str, ...] = (
    "bucket",
    "count",
    "avg_probability",
    "empirical_hit_rate",
)


def validate_prediction_columns(predictions_df: pd.DataFrame) -> None:
    """Validate that prediction rows contain the dashboard-required columns."""
    if not isinstance(predictions_df, pd.DataFrame):
        raise ValueError("predictions_df must be a pandas DataFrame")

    missing_columns = [
        column for column in REQUIRED_PREDICTION_COLUMNS if column not in predictions_df.columns
    ]
    if missing_columns:
        raise ValueError(f"predictions_df is missing required columns: {missing_columns}")


def prepare_predictions_table(
    predictions_df: pd.DataFrame,
    target_type: str | None = None,
    top_k: int = 20,
) -> pd.DataFrame:
    """Return a sorted, display-ready prediction table."""
    _validate_top_k(top_k)
    validate_prediction_columns(predictions_df)

    df = predictions_df.copy(deep=True)
    df["candidate_number"] = df["candidate_number"].astype(str)

    if target_type is not None:
        df = df[df["target_type"] == target_type].copy()

    df["_rank_sort"] = _numeric_column(df, "rank")
    df["_probability_sort"] = _numeric_column(df, "probability")
    df = df[df["_rank_sort"] <= top_k].copy()

    sort_columns: list[str] = []
    if "target_date" in df.columns:
        sort_columns.append("target_date")
    sort_columns.extend(["_rank_sort", "candidate_number"])
    df = df.sort_values(sort_columns, kind="mergesort").reset_index(drop=True)

    display_columns = [column for column in PREDICTION_DISPLAY_COLUMNS if column in df.columns]
    return df[display_columns].copy()


def prepare_probability_distribution(predictions_df: pd.DataFrame) -> pd.DataFrame:
    """Return deterministic probability bucket counts for charting."""
    validate_prediction_columns(predictions_df)
    df = predictions_df.copy(deep=True)
    probabilities = _numeric_column(df, "probability").clip(lower=0.0, upper=1.0)

    counts = {bucket: 0 for bucket in range(10)}
    for probability in probabilities:
        bucket = min(int(float(probability) * 10), 9)
        counts[bucket] += 1

    rows = []
    for bucket in range(10):
        bucket_start = bucket / 10
        bucket_end = (bucket + 1) / 10
        rows.append(
            {
                "probability_bucket": f"{bucket_start:.1f}-{bucket_end:.1f}",
                "bucket_start": bucket_start,
                "bucket_end": bucket_end,
                "count": counts[bucket],
            }
        )
    return pd.DataFrame(rows)


def prepare_topk_summary(summary_dict_or_df: dict[str, Any] | pd.DataFrame) -> pd.DataFrame:
    """Return a chart-ready table of top-k backtest metrics."""
    if isinstance(summary_dict_or_df, pd.DataFrame):
        return summary_dict_or_df.copy(deep=True)
    if not isinstance(summary_dict_or_df, dict):
        raise ValueError("summary_dict_or_df must be a dict or pandas DataFrame")

    summary = dict(summary_dict_or_df)
    nested_summary = summary.get("summary")
    if isinstance(nested_summary, dict):
        merged_summary = {
            key: value for key, value in summary.items() if key != "summary"
        }
        merged_summary.update(nested_summary)
        summary = merged_summary

    metric_prefixes = {
        "precision_at_": "precision",
        "hit_rate_at_": "hit_rate",
        "avg_hits_at_": "avg_hits",
        "recall_at_": "recall",
    }
    top_k_values: set[int] = set()
    for key in summary:
        for prefix in metric_prefixes:
            if key.startswith(prefix):
                suffix = key.removeprefix(prefix)
                if suffix.isdigit():
                    top_k_values.add(int(suffix))

    if top_k_values:
        rows = []
        for top_k in sorted(top_k_values):
            row: dict[str, Any] = {"top_k": top_k}
            for prefix, output_column in metric_prefixes.items():
                row[output_column] = summary.get(f"{prefix}{top_k}")
            rows.append(row)
        return pd.DataFrame(rows, columns=["top_k", "precision", "hit_rate", "avg_hits", "recall"])

    scalar_rows = [
        {"metric": key, "value": value}
        for key, value in sorted(summary.items())
        if not isinstance(value, (dict, list, tuple))
    ]
    return pd.DataFrame(scalar_rows, columns=["metric", "value"])


def prepare_calibration_table(calibration_df: pd.DataFrame) -> pd.DataFrame:
    """Return calibration rows with the expected columns preserved."""
    if not isinstance(calibration_df, pd.DataFrame):
        raise ValueError("calibration_df must be a pandas DataFrame")

    missing_columns = [
        column for column in CALIBRATION_COLUMNS if column not in calibration_df.columns
    ]
    if missing_columns:
        raise ValueError(f"calibration_df is missing required columns: {missing_columns}")
    return calibration_df.loc[:, list(CALIBRATION_COLUMNS)].copy(deep=True)


def run_dashboard() -> bool:
    """Run the local Streamlit dashboard if Streamlit is installed."""
    st = _load_streamlit()
    if st is None:
        return False

    st.set_page_config(page_title="XSMB ML Dashboard", layout="wide")
    st.title("XSMB ML Dashboard")
    st.warning(DISCLAIMER)

    selected_target_type = st.sidebar.selectbox("target_type", list(TARGET_TYPES))
    top_k = st.sidebar.number_input("top_k", min_value=1, value=20, step=1)

    predictions_upload = st.file_uploader("Predictions CSV", type=["csv"])
    predictions_table: pd.DataFrame | None = None
    if predictions_upload is None:
        st.info("Upload a local predictions CSV to view rankings.")
    else:
        try:
            predictions_df = _read_predictions_csv(predictions_upload)
            predictions_table = prepare_predictions_table(
                predictions_df,
                target_type=selected_target_type,
                top_k=int(top_k),
            )
            st.subheader("Latest Predictions")
            st.dataframe(predictions_table, use_container_width=True)

            distribution = prepare_probability_distribution(predictions_df)
            st.subheader("Probability Distribution")
            st.bar_chart(distribution, x="probability_bucket", y="count")
        except ValueError as exc:
            st.error(str(exc))

    summary_upload = st.file_uploader("Backtest summary JSON or CSV", type=["json", "csv"])
    if summary_upload is not None:
        try:
            summary_payload = _read_summary_upload(summary_upload)
            topk_summary = prepare_topk_summary(summary_payload)
            st.subheader("Top-k Performance Comparison")
            st.dataframe(topk_summary, use_container_width=True)
        except (json.JSONDecodeError, ValueError) as exc:
            st.error(str(exc))
    elif predictions_table is None:
        st.info("Upload a backtest summary file to compare top-k performance.")

    calibration_upload = st.file_uploader("Calibration CSV", type=["csv"])
    if calibration_upload is not None:
        try:
            calibration = prepare_calibration_table(pd.read_csv(calibration_upload))
            st.subheader("Calibration Chart")
            st.dataframe(calibration, use_container_width=True)
            st.line_chart(calibration, x="avg_probability", y="empirical_hit_rate")
        except ValueError as exc:
            st.error(str(exc))

    return True


def main() -> None:
    """CLI entry point for `streamlit run xsmb/dashboard/streamlit_app.py`."""
    run_dashboard()


def _validate_top_k(top_k: int) -> None:
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
        raise ValueError("top_k must be a positive integer")


def _numeric_column(df: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_numeric(df[column], errors="coerce")
    if values.isna().any():
        raise ValueError(f"{column} must contain numeric values")
    return values


def _load_streamlit() -> Any | None:
    try:
        import streamlit as st  # type: ignore
    except ImportError:
        return None
    return st


def _read_predictions_csv(uploaded_file: Any) -> pd.DataFrame:
    return pd.read_csv(
        uploaded_file,
        dtype={
            "target_date": str,
            "target_type": str,
            "candidate_number": str,
            "model_name": str,
        },
    )


def _read_summary_upload(uploaded_file: Any) -> dict[str, Any] | pd.DataFrame:
    file_name = getattr(uploaded_file, "name", "")
    if file_name.endswith(".json"):
        raw_payload = uploaded_file.getvalue().decode("utf-8")
        return json.loads(raw_payload)
    return pd.read_csv(uploaded_file)


if __name__ == "__main__":
    main()
