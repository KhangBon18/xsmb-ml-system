"""Tests for leakage-safe feature engineering."""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import pytest

from xsmb.config import (
    TARGET_DB_2CANG,
    TARGET_DB_3CANG,
    TARGET_LOTO_2D_ALL_PRIZES,
)
from xsmb.features.build_dataset import OUTPUT_COLUMNS, build_feature_dataset


def _rows_for_dates(
    target_type: str,
    candidates: list[str],
    num_dates: int,
    hits: dict[str, dict[int, tuple[int, int]]],
) -> list[dict[str, object]]:
    start = date(2024, 1, 1)
    rows: list[dict[str, object]] = []
    for day_index in range(num_dates):
        draw_date = (start + timedelta(days=day_index)).isoformat()
        for candidate in candidates:
            label, hit_count = hits.get(candidate, {}).get(day_index, (0, 0))
            rows.append(
                {
                    "draw_date": draw_date,
                    "target_type": target_type,
                    "candidate_number": candidate,
                    "label": label,
                    "hit_count": hit_count,
                }
            )
    return rows


def _base_history(target_type: str = TARGET_LOTO_2D_ALL_PRIZES) -> pd.DataFrame:
    return pd.DataFrame(
        _rows_for_dates(
            target_type=target_type,
            candidates=["05", "00"],
            num_dates=8,
            hits={
                "05": {
                    1: (1, 2),
                    4: (1, 3),
                    7: (1, 99),
                }
            },
        )
    )


def test_build_feature_dataset_returns_expected_columns() -> None:
    features = build_feature_dataset(
        _base_history(),
        TARGET_LOTO_2D_ALL_PRIZES,
        min_history_days=7,
    )

    assert list(features.columns) == OUTPUT_COLUMNS


@pytest.mark.parametrize(
    ("target_type", "candidate"),
    [
        (TARGET_LOTO_2D_ALL_PRIZES, "05"),
        (TARGET_DB_2CANG, "05"),
        (TARGET_DB_3CANG, "008"),
    ],
)
def test_build_feature_dataset_works_for_all_target_types(
    target_type: str, candidate: str
) -> None:
    history = pd.DataFrame(
        _rows_for_dates(
            target_type=target_type,
            candidates=[candidate],
            num_dates=4,
            hits={candidate: {1: (1, 1), 3: (1, 1)}},
        )
    )

    features = build_feature_dataset(history, target_type, min_history_days=2)

    assert not features.empty
    assert set(features["target_type"]) == {target_type}
    assert candidate in set(features["candidate_number"])


def test_candidate_number_remains_string_and_leading_zeros_are_preserved() -> None:
    history = pd.concat(
        [
            _base_history(),
            pd.DataFrame(
                _rows_for_dates(
                    target_type=TARGET_DB_3CANG,
                    candidates=["008"],
                    num_dates=4,
                    hits={"008": {1: (1, 1)}},
                )
            ),
        ],
        ignore_index=True,
    )

    loto_features = build_feature_dataset(
        history, TARGET_LOTO_2D_ALL_PRIZES, min_history_days=7
    )
    db_3_features = build_feature_dataset(history, TARGET_DB_3CANG, min_history_days=2)

    assert set(loto_features["candidate_number"]) == {"00", "05"}
    assert set(db_3_features["candidate_number"]) == {"008"}
    assert all(isinstance(value, str) for value in db_3_features["candidate_number"])


def test_frequency_windows_count_only_dates_before_target_date() -> None:
    features = build_feature_dataset(
        _base_history(),
        TARGET_LOTO_2D_ALL_PRIZES,
        min_history_days=7,
    )
    row = features[
        (features["target_date"] == "2024-01-08")
        & (features["candidate_number"] == "05")
    ].iloc[0]

    assert row["freq_7"] == 2
    assert row["freq_14"] == 2
    assert row["freq_30"] == 2


def test_explicit_no_leakage_excludes_target_date_hit() -> None:
    history = pd.DataFrame(
        _rows_for_dates(
            target_type=TARGET_LOTO_2D_ALL_PRIZES,
            candidates=["05"],
            num_dates=8,
            hits={"05": {7: (1, 9)}},
        )
    )

    features = build_feature_dataset(
        history, TARGET_LOTO_2D_ALL_PRIZES, min_history_days=7
    )
    row = features.iloc[0]

    assert row["label"] == 1
    assert row["freq_7"] == 0
    assert row["freq_30"] == 0
    assert row["rolling_hit_rate_30"] == 0.0


def test_hit_count_sum_30_uses_only_prior_dates() -> None:
    features = build_feature_dataset(
        _base_history(),
        TARGET_LOTO_2D_ALL_PRIZES,
        min_history_days=7,
    )
    row = features[
        (features["target_date"] == "2024-01-08")
        & (features["candidate_number"] == "05")
    ].iloc[0]

    assert row["hit_count_sum_30"] == 5
    assert row["hit_count"] == 99


def test_gap_features_are_deterministic_and_prior_only() -> None:
    features = build_feature_dataset(
        _base_history(),
        TARGET_LOTO_2D_ALL_PRIZES,
        min_history_days=7,
    )
    hit_candidate = features[
        (features["target_date"] == "2024-01-08")
        & (features["candidate_number"] == "05")
    ].iloc[0]
    never_seen = features[
        (features["target_date"] == "2024-01-08")
        & (features["candidate_number"] == "00")
    ].iloc[0]

    assert hit_candidate["current_gap"] == 2
    assert hit_candidate["days_since_last_seen"] == 2
    assert hit_candidate["max_gap_before_target"] == 2
    assert hit_candidate["avg_gap_before_target"] == 2.0
    assert never_seen["current_gap"] == 7
    assert never_seen["days_since_last_seen"] == 7
    assert never_seen["max_gap_before_target"] == 7
    assert never_seen["avg_gap_before_target"] == 7.0


def test_rolling_hit_rates_use_available_prior_window_denominator() -> None:
    features = build_feature_dataset(
        _base_history(),
        TARGET_LOTO_2D_ALL_PRIZES,
        min_history_days=7,
    )
    row = features[
        (features["target_date"] == "2024-01-08")
        & (features["candidate_number"] == "05")
    ].iloc[0]

    assert row["rolling_hit_rate_30"] == pytest.approx(2 / 7)
    assert row["rolling_hit_rate_90"] == pytest.approx(2 / 7)


def test_min_history_days_suppresses_early_dates() -> None:
    history = pd.DataFrame(
        _rows_for_dates(
            target_type=TARGET_DB_2CANG,
            candidates=["05"],
            num_dates=35,
            hits={"05": {0: (1, 1), 31: (1, 1)}},
        )
    )

    features = build_feature_dataset(history, TARGET_DB_2CANG, min_history_days=30)

    assert features["target_date"].min() == "2024-01-31"


def test_start_date_and_end_date_filters_work() -> None:
    history = pd.DataFrame(
        _rows_for_dates(
            target_type=TARGET_DB_2CANG,
            candidates=["05"],
            num_dates=12,
            hits={},
        )
    )

    features = build_feature_dataset(
        history,
        TARGET_DB_2CANG,
        start_date="2024-01-06",
        end_date="2024-01-08",
        min_history_days=2,
    )

    assert list(features["target_date"]) == [
        "2024-01-06",
        "2024-01-07",
        "2024-01-08",
    ]


def test_build_feature_dataset_does_not_mutate_input_dataframe() -> None:
    history = _base_history()
    original = history.copy(deep=True)

    build_feature_dataset(history, TARGET_LOTO_2D_ALL_PRIZES, min_history_days=7)

    pd.testing.assert_frame_equal(history, original)


def test_output_order_is_target_date_then_candidate_number() -> None:
    history = pd.DataFrame(
        _rows_for_dates(
            target_type=TARGET_LOTO_2D_ALL_PRIZES,
            candidates=["05", "00"],
            num_dates=4,
            hits={},
        )
    )

    features = build_feature_dataset(
        history, TARGET_LOTO_2D_ALL_PRIZES, min_history_days=2
    )

    assert list(features[["target_date", "candidate_number"]].itertuples(index=False, name=None)) == [
        ("2024-01-03", "00"),
        ("2024-01-03", "05"),
        ("2024-01-04", "00"),
        ("2024-01-04", "05"),
    ]


def test_unsupported_target_type_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unsupported target_type"):
        build_feature_dataset(_base_history(), "unsupported", min_history_days=1)


def test_missing_required_columns_raise_clear_value_error() -> None:
    history = _base_history().drop(columns=["hit_count"])

    with pytest.raises(ValueError, match="missing required columns"):
        build_feature_dataset(history, TARGET_LOTO_2D_ALL_PRIZES, min_history_days=1)
