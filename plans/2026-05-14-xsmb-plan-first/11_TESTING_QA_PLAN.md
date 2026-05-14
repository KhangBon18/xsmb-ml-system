# 11 — Testing and QA Plan

---

## 1. Testing Framework

- **Framework:** `pytest`
- **Coverage tool:** `pytest-cov` (optional cho report)
- **Test location:** `tests/`
- **Naming convention:** `test_<module>.py`
- **Run:** `pytest tests/ -v`

---

## 2. Test Checklist

### 2.1. Parser Tests (`tests/test_parser.py`)

| ID | Test | Mô tả | Priority |
|:---|:---|:---|:---|
| P1 | `test_parse_valid_html` | Parse 1 trang HTML hợp lệ → 27 PrizeEntry | 🔴 MUST |
| P2 | `test_parse_all_prize_tiers` | Mỗi tier có đúng count entries | 🔴 MUST |
| P3 | `test_parse_digit_lengths` | Mỗi winning_number có đúng số chữ số | 🔴 MUST |
| P4 | `test_parse_preserves_leading_zeros` | "00512" → winning_number="00512" | 🔴 MUST |
| P5 | `test_parse_raises_on_missing_tier` | HTML thiếu giải → ParseError | 🟡 SHOULD |
| P6 | `test_parse_raises_on_extra_entries` | >27 entries → ParseError | 🟡 SHOULD |
| P7 | `test_parse_raises_on_non_digit` | Ký tự lạ → ParseError | 🟡 SHOULD |

### 2.2. Normalize Tests (`tests/test_normalize.py`)

| ID | Test | Mô tả | Priority |
|:---|:---|:---|:---|
| N1 | `test_normalize_prize_tier_standard` | "special" → "special" | 🔴 MUST |
| N2 | `test_normalize_prize_tier_alias` | "gdb" → "special", "g7" → "seventh" | 🔴 MUST |
| N3 | `test_normalize_winning_number_strip` | " 45678 " → "45678" | 🔴 MUST |
| N4 | `test_normalize_winning_number_non_digit` | "45a78" → ValueError | 🔴 MUST |
| N5 | `test_leading_zero_preserved` | "00512" normalized → "00512" | 🔴 MUST |

### 2.3. Transform / Extraction Tests (`tests/test_transform.py`) [NEW]

| ID | Test | Mô tả | Priority |
|:---|:---|:---|:---|
| T1 | `test_extract_loto_2d` | "45678" → "78", "105" → "05", "02" → "02" | 🔴 MUST |
| T2 | `test_extract_db_2cang` | "45678" → "78", "00512" → "12" | 🔴 MUST |
| T3 | `test_extract_db_3cang` | "45678" → "678", "00512" → "512", "45008" → "008" | 🔴 MUST |
| T4 | `test_extract_leading_zero_edge` | "10005" → loto="05", "00100" → loto="00" | 🔴 MUST |
| T5 | `test_build_targets_loto_2d_100_rows` | 27 entries → 100 target rows | 🔴 MUST |
| T6 | `test_build_targets_loto_2d_labels` | label=1 cho numbers có trong entries | 🔴 MUST |
| T7 | `test_build_targets_loto_2d_actual_hits` | Đếm số nháy đúng | 🔴 MUST |
| T8 | `test_build_targets_db_2d_100_rows` | → 100 rows, chỉ 1 label=1 | 🔴 MUST |
| T9 | `test_build_targets_db_3d_1000_rows` | → 1000 rows, chỉ 1 label=1 | 🔴 MUST |
| T10 | `test_targets_not_mixed` | loto_2d target ≠ db_2d target | 🔴 MUST |

### 2.4. Leading Zero Tests (cross-module)

| ID | Test | Mô tả | Priority |
|:---|:---|:---|:---|
| LZ1 | `test_loto_number_always_2_chars` | Mọi loto_number có len=2 | 🔴 MUST |
| LZ2 | `test_db_3d_number_always_3_chars` | Mọi db_3d number có len=3 | 🔴 MUST |
| LZ3 | `test_number_is_string_not_int` | `type(number) == str` | 🔴 MUST |
| LZ4 | `test_zero_padded_numbers` | "00", "01", "09" được xử lý đúng | 🔴 MUST |

### 2.5. Validation Tests (`tests/test_validate.py`) [NEW]

| ID | Test | Mô tả | Priority |
|:---|:---|:---|:---|
| V1 | `test_validate_27_prizes_pass` | 27 entries hợp lệ → valid | 🔴 MUST |
| V2 | `test_validate_26_prizes_fail` | 26 entries → invalid | 🔴 MUST |
| V3 | `test_validate_28_prizes_fail` | 28 entries → invalid | 🔴 MUST |
| V4 | `test_validate_wrong_digit_length` | special có 4 chữ số → invalid | 🔴 MUST |
| V5 | `test_validate_non_digit` | "45a78" → invalid | 🟡 SHOULD |

### 2.6. Feature Tests (`tests/test_features.py`)

| ID | Test | Mô tả | Priority |
|:---|:---|:---|:---|
| F1 | `test_no_future_leakage` | Features cho date T chỉ dùng data < T | 🔴 MUST |
| F2 | `test_frequency_feature_window` | freq_30 đếm đúng 30 kỳ | 🔴 MUST |
| F3 | `test_gap_feature_current` | current_gap đúng | 🔴 MUST |
| F4 | `test_gap_feature_max` | max_gap đúng | 🟡 SHOULD |
| F5 | `test_gap_never_appeared` | Number chưa bao giờ ra → gap = total | 🟡 SHOULD |
| F6 | `test_rolling_hits_counts_multi_hits` | 3 nháy 1 ngày → counted | 🟡 SHOULD |
| F7 | `test_feature_column_consistency` | Output columns match expected list | 🔴 MUST |

### 2.7. Baseline Tests (`tests/test_baseline.py`) [NEW]

| ID | Test | Mô tả | Priority |
|:---|:---|:---|:---|
| B1 | `test_random_baseline_uniform` | All probabilities equal | 🔴 MUST |
| B2 | `test_random_baseline_output_size` | 100 items cho loto_2d, 1000 cho db_3d | 🔴 MUST |
| B3 | `test_freq_baseline_ranking` | Số freq cao → probability cao | 🔴 MUST |
| B4 | `test_baseline_deterministic` | Cùng input → cùng output | 🔴 MUST |
| B5 | `test_baseline_probabilities_valid` | 0 ≤ P ≤ 1 | 🔴 MUST |

### 2.8. Backtest Tests (`tests/test_backtest.py`)

| ID | Test | Mô tả | Priority |
|:---|:---|:---|:---|
| BT1 | `test_backtest_no_random_split` | Train dates < test dates always | 🔴 MUST |
| BT2 | `test_backtest_expanding_window` | Train set grows over time | 🔴 MUST |
| BT3 | `test_backtest_metrics_computed` | Brier, P@K, Hit@K returned | 🔴 MUST |
| BT4 | `test_backtest_report_csv_format` | CSV headers match spec | 🟡 SHOULD |
| BT5 | `test_backtest_includes_baseline` | Baseline results included | 🟡 SHOULD |

### 2.9. Metrics Tests (`tests/test_metrics.py`) [NEW]

| ID | Test | Mô tả | Priority |
|:---|:---|:---|:---|
| M1 | `test_brier_score_perfect` | y=[1,0], p=[1,0] → score=0 | 🔴 MUST |
| M2 | `test_brier_score_worst` | y=[1,0], p=[0,1] → score=1 | 🔴 MUST |
| M3 | `test_precision_at_k` | Manual example → correct | 🔴 MUST |
| M4 | `test_hit_rate_at_k` | ≥1 hit → 1.0, 0 hits → 0.0 | 🔴 MUST |

### 2.10. CLI Smoke Tests (`tests/test_cli.py`) [NEW]

| ID | Test | Mô tả | Priority |
|:---|:---|:---|:---|
| C1 | `test_cli_help` | `--help` exits 0 | 🟡 SHOULD |
| C2 | `test_cli_init_db` | `init-db` creates DB file | 🟡 SHOULD |
| C3 | `test_cli_unknown_command` | Unknown command → error | 🟡 SHOULD |

---

## 3. Test Data Strategy

### 3.1. Fixtures

- Tạo `tests/fixtures/` chứa:
  - `sample_html_valid.html` — 1 trang XSMB hợp lệ.
  - `sample_html_missing.html` — Thiếu giải.
  - `sample_draw_data.json` — Parsed draw data cho test.

### 3.2. Conftest

```python
# tests/conftest.py

import pytest
import sqlite3
from xsmb.database.connection import get_connection, init_db

@pytest.fixture
def test_db(tmp_path):
    """Create a temporary test database."""
    db_path = tmp_path / "test.db"
    init_db(db_path)
    conn = get_connection(db_path)
    yield conn
    conn.close()

@pytest.fixture
def sample_prizes():
    """Return a valid list of 27 PrizeEntry objects."""
    ...
```

---

## 4. QA Checklist (Manual)

- [ ] Crawl 1 ngày → raw HTML saved → parse → 27 entries.
- [ ] Process 1 tháng → all dates validated.
- [ ] Build features → no leakage error.
- [ ] Train logistic on loto_2d → model file saved.
- [ ] Predict 1 ngày → 100 ranked numbers output.
- [ ] Backtest 1 tháng → CSV report generated.
- [ ] Compare logistic vs random baseline → metrics table.

---

## 5. New Test Files to Create

| File | Status | Tests |
|:---|:---|:---|
| `tests/test_parser.py` | Exists (empty) | P1-P7 |
| `tests/test_normalize.py` | Exists (empty) | N1-N5 |
| `tests/test_transform.py` | **NEW** | T1-T10, LZ1-LZ4 |
| `tests/test_validate.py` | **NEW** | V1-V5 |
| `tests/test_features.py` | Exists (empty) | F1-F7 |
| `tests/test_baseline.py` | **NEW** | B1-B5 |
| `tests/test_backtest.py` | Exists (empty) | BT1-BT5 |
| `tests/test_metrics.py` | **NEW** | M1-M4 |
| `tests/test_cli.py` | **NEW** | C1-C3 |
| `tests/conftest.py` | **NEW** | Fixtures |
