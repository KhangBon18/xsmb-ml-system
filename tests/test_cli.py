"""Tests for the CLI in app.main (Phase 7A skeleton + Phase 7B wiring)."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from datetime import date, timedelta

import pandas as pd
import pytest

from app.main import build_parser, main
from xsmb.config import TARGET_TYPES


# ===========================================================================
# Phase 7A — skeleton tests
# ===========================================================================


# ---------------------------------------------------------------------------
# Help output
# ---------------------------------------------------------------------------

class TestHelp:
    """Verify help text for the top-level and each subcommand."""

    def test_top_level_help_returns_zero(self) -> None:
        """--help should exit with code 0."""
        with pytest.raises(SystemExit, match="0"):
            main(["--help"])

    def test_no_command_returns_one(self) -> None:
        """Calling with no command should return 1 (not crash)."""
        assert main([]) == 1

    @pytest.mark.parametrize(
        "command",
        ["scrape", "process", "build-features", "backtest", "train", "predict"],
    )
    def test_subcommand_help_exits_zero(self, command: str) -> None:
        with pytest.raises(SystemExit, match="0"):
            main([command, "--help"])


# ---------------------------------------------------------------------------
# Target type validation
# ---------------------------------------------------------------------------

class TestTargetTypeValidation:
    """argparse choices should reject invalid target_type values."""

    @pytest.mark.parametrize(
        "command_args",
        [
            ["build-features", "--target-type", "invalid_type"],
            ["backtest", "--target-type", "invalid_type", "--model", "frequency_30"],
            ["train", "--target-type", "invalid_type", "--model", "logistic_regression"],
            ["predict", "--target-date", "2024-01-01", "--target-type", "invalid_type"],
        ],
    )
    def test_invalid_target_type_rejected(self, command_args: list[str]) -> None:
        """Commands with an unknown target_type should fail."""
        with pytest.raises(SystemExit) as exc_info:
            main(command_args)
        # argparse exits with code 2 for usage errors.
        assert exc_info.value.code == 2

    @pytest.mark.parametrize("target_type", TARGET_TYPES)
    def test_build_features_accepts_valid_target_types(self, target_type: str) -> None:
        code = main(["build-features", "--target-type", target_type])
        assert code == 0


# ---------------------------------------------------------------------------
# top_k validation
# ---------------------------------------------------------------------------

class TestTopKValidation:
    """--top-k must be a positive integer."""

    def test_top_k_zero_rejected(self) -> None:
        with pytest.raises(SystemExit):
            main([
                "predict", "--target-date", "2024-01-01",
                "--target-type", "loto_2d_all_prizes", "--top-k", "0",
            ])

    def test_top_k_negative_rejected(self) -> None:
        with pytest.raises(SystemExit):
            main([
                "predict", "--target-date", "2024-01-01",
                "--target-type", "loto_2d_all_prizes", "--top-k", "-5",
            ])

    def test_top_k_non_integer_rejected(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main([
                "predict", "--target-date", "2024-01-01",
                "--target-type", "loto_2d_all_prizes", "--top-k", "abc",
            ])
        assert exc_info.value.code == 2

    def test_top_k_positive_accepted(self) -> None:
        code = main([
            "predict", "--target-date", "2024-01-01",
            "--target-type", "loto_2d_all_prizes", "--top-k", "10",
        ])
        assert code == 0


# ---------------------------------------------------------------------------
# Date validation
# ---------------------------------------------------------------------------

class TestDateValidation:
    """Dates must follow YYYY-MM-DD and be real calendar dates."""

    def test_scrape_invalid_date_format(self) -> None:
        with pytest.raises(SystemExit):
            main(["scrape", "--start-date", "01-01-2024", "--end-date", "2024-01-31"])

    def test_scrape_impossible_date(self) -> None:
        with pytest.raises(SystemExit):
            main(["scrape", "--start-date", "2024-02-30", "--end-date", "2024-03-01"])

    def test_predict_invalid_target_date(self) -> None:
        with pytest.raises(SystemExit):
            main([
                "predict", "--target-date", "not-a-date",
                "--target-type", "loto_2d_all_prizes",
            ])

    def test_scrape_valid_dates_accepted(self) -> None:
        code = main(["scrape", "--start-date", "2024-01-01", "--end-date", "2024-01-31"])
        assert code == 0

    def test_process_valid_dates_accepted(self) -> None:
        code = main(["process", "--start-date", "2024-06-01", "--end-date", "2024-06-30"])
        assert code == 0


# ---------------------------------------------------------------------------
# Safe no-network / no-DB behaviour
# ---------------------------------------------------------------------------

class TestNoSideEffects:
    """MVP stubs must not perform network requests or create real databases."""

    def test_scrape_prints_stub_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["scrape", "--start-date", "2024-01-01", "--end-date", "2024-01-31"])
        assert code == 0
        captured = capsys.readouterr().out
        assert "MVP stub" in captured
        assert "no network" in captured.lower()

    def test_process_prints_stub_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["process", "--start-date", "2024-01-01", "--end-date", "2024-01-31"])
        assert code == 0
        captured = capsys.readouterr().out
        assert "MVP stub" in captured

    def test_build_features_prints_stub_message(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        code = main(["build-features", "--target-type", "loto_2d_all_prizes"])
        assert code == 0
        captured = capsys.readouterr().out
        assert "MVP stub" in captured

    def test_backtest_prints_stub_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["backtest", "--target-type", "db_2cang", "--model", "frequency_30"])
        assert code == 0
        captured = capsys.readouterr().out
        assert "MVP stub" in captured

    def test_train_prints_stub_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main(["train", "--target-type", "db_2cang", "--model", "logistic_regression"])
        assert code == 0
        captured = capsys.readouterr().out
        assert "MVP stub" in captured

    def test_predict_prints_stub_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        code = main([
            "predict", "--target-date", "2024-01-01",
            "--target-type", "db_3cang", "--top-k", "20",
        ])
        assert code == 0
        captured = capsys.readouterr().out
        assert "MVP stub" in captured

    def test_no_real_db_created(self, tmp_path: object) -> None:
        """Running all commands should not create data/xsmb.sqlite3."""
        db_path = pathlib.Path("data/xsmb.sqlite3")
        existed_before = db_path.exists()
        main(["scrape", "--start-date", "2024-01-01", "--end-date", "2024-01-01"])
        main(["process", "--start-date", "2024-01-01", "--end-date", "2024-01-01"])
        main(["build-features", "--target-type", "loto_2d_all_prizes"])
        main(["backtest", "--target-type", "loto_2d_all_prizes", "--model", "frequency_30"])
        main(["train", "--target-type", "loto_2d_all_prizes", "--model", "logistic_regression"])
        main([
            "predict", "--target-date", "2024-01-01",
            "--target-type", "loto_2d_all_prizes", "--top-k", "5",
        ])
        if not existed_before:
            assert not db_path.exists(), "CLI stubs must not create the real database"


# ---------------------------------------------------------------------------
# Model name validation
# ---------------------------------------------------------------------------

class TestModelValidation:
    """Verify that argparse choices reject invalid model names."""

    def test_backtest_invalid_model_rejected(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["backtest", "--target-type", "loto_2d_all_prizes", "--model", "fake_model"])
        assert exc_info.value.code == 2

    def test_train_invalid_model_rejected(self) -> None:
        with pytest.raises(SystemExit) as exc_info:
            main(["train", "--target-type", "loto_2d_all_prizes", "--model", "fake_model"])
        assert exc_info.value.code == 2


# ---------------------------------------------------------------------------
# Leading zero preservation in candidate_number strings
# ---------------------------------------------------------------------------

class TestLeadingZeroPreservation:
    """Target type values must stay as strings — never cast to int."""

    def test_target_types_are_strings(self) -> None:
        for tt in TARGET_TYPES:
            assert isinstance(tt, str)

    def test_predict_preserves_target_type_string(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The predict stub should echo back the exact target_type string."""
        code = main([
            "predict", "--target-date", "2024-01-01",
            "--target-type", "db_3cang", "--top-k", "5",
        ])
        assert code == 0
        out = capsys.readouterr().out
        assert "db_3cang" in out


# ---------------------------------------------------------------------------
# Module runnable guard
# ---------------------------------------------------------------------------

class TestModuleRunnable:
    """Verify the module is runnable with python -m app.main."""

    def test_module_runnable_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "app.main", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "xsmb-ml" in result.stdout.lower() or "usage" in result.stdout.lower()

    def test_module_runnable_no_args(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "app.main"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 1


# ===========================================================================
# Phase 7B — CSV-wired command tests
# ===========================================================================


# ---------------------------------------------------------------------------
# Synthetic data helpers
# ---------------------------------------------------------------------------

_LOTO_CANDIDATES = [f"{n:02d}" for n in range(100)]
_DB3_CANDIDATES = [f"{n:03d}" for n in range(1000)]
_FEATURE_COLS = [
    "freq_7", "freq_14", "freq_30", "freq_60", "freq_90", "freq_180",
    "hit_count_sum_30", "current_gap", "days_since_last_seen",
    "max_gap_before_target", "avg_gap_before_target",
    "rolling_hit_rate_30", "rolling_hit_rate_90",
]


def _make_history_df(
    num_dates: int = 40,
    target_type: str = "loto_2d_all_prizes",
) -> pd.DataFrame:
    """Build a synthetic history DataFrame for backtest with leading-zero candidates.

    Returns one row per candidate per date (100 candidates × num_dates dates).
    """
    base = date(2024, 1, 1)
    rows = []
    for day_offset in range(num_dates):
        draw_date = (base + timedelta(days=day_offset)).isoformat()
        for candidate in _LOTO_CANDIDATES:
            label = 1 if int(candidate) % 10 == day_offset % 10 else 0
            hit_count = label
            rows.append({
                "draw_date": draw_date,
                "target_type": target_type,
                "candidate_number": candidate,
                "label": label,
                "hit_count": hit_count,
            })
    return pd.DataFrame(rows)


def _make_feature_df(
    num_dates: int = 40,
    target_type: str = "loto_2d_all_prizes",
    candidates: list[str] | None = None,
) -> pd.DataFrame:
    """Build a synthetic feature DataFrame for train/predict with leading zeros.

    Contains target_date, target_type, candidate_number, label, hit_count,
    plus all FEATURE_COLS with deterministic numeric values.
    """
    if candidates is None:
        candidates = _LOTO_CANDIDATES

    base = date(2024, 1, 1)
    rows = []
    for day_offset in range(num_dates):
        target_date = (base + timedelta(days=day_offset)).isoformat()
        for idx, candidate in enumerate(candidates):
            label = 1 if idx % 10 == day_offset % 10 else 0
            hit_count = label
            row = {
                "target_date": target_date,
                "target_type": target_type,
                "candidate_number": candidate,
                "label": label,
                "hit_count": hit_count,
            }
            # Deterministic numeric features.
            for col in _FEATURE_COLS:
                if "freq" in col:
                    row[col] = (idx + day_offset) % 30
                elif "gap" in col:
                    row[col] = (idx + 1) + day_offset % 5
                elif "rolling" in col:
                    row[col] = round(0.1 + 0.005 * idx, 4)
                elif "hit_count_sum" in col:
                    row[col] = label * 2
                elif "days_since" in col:
                    row[col] = idx + 1
                else:
                    row[col] = 0.0
            rows.append(row)
    return pd.DataFrame(rows)


def _write_csv(df: pd.DataFrame, path: pathlib.Path) -> str:
    """Write DataFrame to CSV, forcing candidate_number as string."""
    df.to_csv(path, index=False)
    return str(path)


# ---------------------------------------------------------------------------
# Backtest with --history-csv
# ---------------------------------------------------------------------------

class TestBacktestCSV:
    """backtest --history-csv should call run_walk_forward_backtest and emit JSON."""

    def test_backtest_with_history_csv(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        history_df = _make_history_df(num_dates=40)
        csv_path = _write_csv(history_df, tmp_path / "history.csv")

        code = main([
            "backtest",
            "--target-type", "loto_2d_all_prizes",
            "--model", "frequency_30",
            "--history-csv", csv_path,
        ])
        assert code == 0

        output = capsys.readouterr().out
        summary = json.loads(output)
        assert summary["target_type"] == "loto_2d_all_prizes"
        assert summary["model_name"] == "frequency_30"
        assert "brier_score" in summary

    def test_backtest_without_csv_stays_stub(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        code = main([
            "backtest",
            "--target-type", "loto_2d_all_prizes",
            "--model", "frequency_30",
        ])
        assert code == 0
        assert "MVP stub" in capsys.readouterr().out

    def test_backtest_missing_csv_fails(self) -> None:
        with pytest.raises(SystemExit):
            main([
                "backtest",
                "--target-type", "loto_2d_all_prizes",
                "--model", "frequency_30",
                "--history-csv", "/nonexistent/path.csv",
            ])


# ---------------------------------------------------------------------------
# Train with --features-csv
# ---------------------------------------------------------------------------

class TestTrainCSV:
    """train --features-csv should call train_model and save_model_artifact."""

    def test_train_with_features_csv(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        feature_df = _make_feature_df(num_dates=10)
        csv_path = _write_csv(feature_df, tmp_path / "features.csv")
        artifact_dir = str(tmp_path / "models")

        code = main([
            "train",
            "--target-type", "loto_2d_all_prizes",
            "--model", "logistic_regression",
            "--features-csv", csv_path,
            "--artifact-dir", artifact_dir,
        ])
        assert code == 0

        output = capsys.readouterr().out
        result = json.loads(output)
        assert result["model_name"] == "logistic_regression"
        assert result["target_type"] == "loto_2d_all_prizes"
        assert result["row_count"] > 0
        assert pathlib.Path(result["artifact_path"]).exists()

    def test_train_without_csv_stays_stub(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        code = main([
            "train",
            "--target-type", "loto_2d_all_prizes",
            "--model", "logistic_regression",
        ])
        assert code == 0
        assert "MVP stub" in capsys.readouterr().out

    def test_train_missing_csv_fails(self) -> None:
        with pytest.raises(SystemExit):
            main([
                "train",
                "--target-type", "loto_2d_all_prizes",
                "--model", "logistic_regression",
                "--features-csv", "/nonexistent/features.csv",
            ])


# ---------------------------------------------------------------------------
# Predict with --features-csv + --artifact
# ---------------------------------------------------------------------------

class TestPredictCSV:
    """predict --features-csv --artifact should call predict_probabilities."""

    def _train_artifact(self, tmp_path: pathlib.Path) -> str:
        """Helper: train and save a model artifact, return its path."""
        from xsmb.models.train import save_model_artifact, train_model

        feature_df = _make_feature_df(num_dates=10)
        trained = train_model(
            feature_df, target_type="loto_2d_all_prizes",
            model_name="logistic_regression",
        )
        return save_model_artifact(trained, artifact_dir=str(tmp_path / "models"))

    def test_predict_with_csv_and_artifact(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        artifact_path = self._train_artifact(tmp_path)
        feature_df = _make_feature_df(num_dates=10)
        csv_path = _write_csv(feature_df, tmp_path / "features.csv")

        code = main([
            "predict",
            "--target-date", "2024-01-05",
            "--target-type", "loto_2d_all_prizes",
            "--top-k", "10",
            "--features-csv", csv_path,
            "--artifact", artifact_path,
        ])
        assert code == 0

        output = capsys.readouterr().out
        records = json.loads(output)
        assert isinstance(records, list)
        assert len(records) <= 10
        for rec in records:
            assert "candidate_number" in rec
            assert "probability" in rec
            assert "rank" in rec
            # candidate_number must be a string.
            assert isinstance(rec["candidate_number"], str)

    def test_predict_without_csv_stays_stub(
        self, capsys: pytest.CaptureFixture[str],
    ) -> None:
        code = main([
            "predict",
            "--target-date", "2024-01-01",
            "--target-type", "loto_2d_all_prizes",
            "--top-k", "5",
        ])
        assert code == 0
        assert "MVP stub" in capsys.readouterr().out

    def test_predict_without_artifact_stays_stub(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        feature_df = _make_feature_df(num_dates=5)
        csv_path = _write_csv(feature_df, tmp_path / "features.csv")
        # --artifact is missing → should stay in stub mode.
        code = main([
            "predict",
            "--target-date", "2024-01-01",
            "--target-type", "loto_2d_all_prizes",
            "--top-k", "5",
            "--features-csv", csv_path,
        ])
        assert code == 0
        assert "MVP stub" in capsys.readouterr().out

    def test_predict_missing_artifact_fails(
        self, tmp_path: pathlib.Path,
    ) -> None:
        feature_df = _make_feature_df(num_dates=5)
        csv_path = _write_csv(feature_df, tmp_path / "features.csv")
        with pytest.raises(SystemExit):
            main([
                "predict",
                "--target-date", "2024-01-01",
                "--target-type", "loto_2d_all_prizes",
                "--features-csv", csv_path,
                "--artifact", "/nonexistent/model.pkl",
            ])

    def test_predict_missing_features_csv_fails(
        self, tmp_path: pathlib.Path,
    ) -> None:
        artifact_path = self._train_artifact(tmp_path)
        with pytest.raises(SystemExit):
            main([
                "predict",
                "--target-date", "2024-01-01",
                "--target-type", "loto_2d_all_prizes",
                "--features-csv", "/nonexistent/features.csv",
                "--artifact", artifact_path,
            ])


# ---------------------------------------------------------------------------
# Leading zero preservation through CLI predict pipeline
# ---------------------------------------------------------------------------

class TestCLIPredictLeadingZeros:
    """Verify that candidate_number leading zeros survive the full CLI pipeline."""

    def test_predict_preserves_00_and_05(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Candidates '00' and '05' must appear as strings with leading zeros."""
        from xsmb.models.train import save_model_artifact, train_model

        feature_df = _make_feature_df(num_dates=10)
        trained = train_model(
            feature_df, target_type="loto_2d_all_prizes",
            model_name="logistic_regression",
        )
        artifact_path = save_model_artifact(
            trained, artifact_dir=str(tmp_path / "models"),
        )
        csv_path = _write_csv(feature_df, tmp_path / "features.csv")

        code = main([
            "predict",
            "--target-date", "2024-01-05",
            "--target-type", "loto_2d_all_prizes",
            "--top-k", "100",
            "--features-csv", csv_path,
            "--artifact", artifact_path,
        ])
        assert code == 0

        records = json.loads(capsys.readouterr().out)
        candidate_numbers = {r["candidate_number"] for r in records}
        # "00" and "05" must survive as two-char strings with leading zeros.
        assert "00" in candidate_numbers, "Leading zero for '00' was lost"
        assert "05" in candidate_numbers, "Leading zero for '05' was lost"
        # No number should be a bare int like 0 or 5.
        for num in candidate_numbers:
            assert isinstance(num, str)
            assert len(num) == 2

    def test_predict_preserves_008_for_db_3cang(
        self, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Candidate '008' for db_3cang must survive as a 3-char string."""
        from xsmb.models.train import save_model_artifact, train_model

        feature_df = _make_feature_df(
            num_dates=10,
            target_type="db_3cang",
            candidates=_DB3_CANDIDATES,
        )
        trained = train_model(
            feature_df, target_type="db_3cang",
            model_name="logistic_regression",
        )
        artifact_path = save_model_artifact(
            trained, artifact_dir=str(tmp_path / "models"),
        )
        csv_path = _write_csv(feature_df, tmp_path / "features.csv")

        code = main([
            "predict",
            "--target-date", "2024-01-05",
            "--target-type", "db_3cang",
            "--top-k", "1000",
            "--features-csv", csv_path,
            "--artifact", artifact_path,
        ])
        assert code == 0

        records = json.loads(capsys.readouterr().out)
        candidate_numbers = {r["candidate_number"] for r in records}
        assert "008" in candidate_numbers, "Leading zeros for '008' were lost"
        assert "000" in candidate_numbers, "Leading zeros for '000' were lost"
        for num in candidate_numbers:
            assert isinstance(num, str)
            assert len(num) == 3


# ---------------------------------------------------------------------------
# No live network / no real DB even with wired commands
# ---------------------------------------------------------------------------

class TestNoSideEffectsPhase7B:
    """CSV-wired commands must not hit the network or create the real DB."""

    def test_wired_commands_no_real_db(self, tmp_path: pathlib.Path) -> None:
        db_path = pathlib.Path("data/xsmb.sqlite3")
        existed_before = db_path.exists()

        history_df = _make_history_df(num_dates=40)
        csv_path = _write_csv(history_df, tmp_path / "history.csv")

        main([
            "backtest",
            "--target-type", "loto_2d_all_prizes",
            "--model", "frequency_30",
            "--history-csv", csv_path,
        ])

        if not existed_before:
            assert not db_path.exists(), "Wired CLI must not create the real database"
