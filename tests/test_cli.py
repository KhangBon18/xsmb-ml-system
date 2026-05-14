"""Tests for the CLI skeleton in app.main (Phase 7A)."""

from __future__ import annotations

import subprocess
import sys

import pytest

from app.main import build_parser, main
from xsmb.config import TARGET_TYPES


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
        import pathlib
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
