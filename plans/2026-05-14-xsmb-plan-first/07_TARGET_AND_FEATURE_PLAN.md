# 07 — Target and Feature Plan

---

## 1. Target Builder Design

### 1.1. Architecture

```
xsmb/features/
├── build_dataset.py          # Orchestrator: build full feature dataset
├── target_builder.py         # [NEW] Target-specific label construction
├── frequency_features.py     # Frequency window features
├── gap_features.py           # Gap/Gan features
└── rolling_features.py       # Rolling statistics features
```

> **Note:** File `target_builder.py` cần thêm mới vào repo. Nó chịu trách nhiệm tách biệt logic tạo target labels cho mỗi target type.

### 1.2. Target Types Summary

| Target Type | Number Range | Rows/Day | Positive/Day | Data Source | Class Imbalance |
|:---|:---|:---|:---|:---|:---|
| `loto_2d` | "00".."99" | 100 | ~23-25 | All 27 prizes | ~1:3.5 |
| `db_2d` | "00".."99" | 100 | 1 | Special prize only | 1:99 |
| `db_3d` | "000".."999" | 1000 | 1 | Special prize only | 1:999 |

---

## 2. Feature Groups

### 2.1. Frequency Features (`frequency_features.py`)

Đếm số lần number xuất hiện trong X kỳ quay gần nhất (**trước** `target_date`).

| Feature Name | Window (draws) | Description |
|:---|:---|:---|
| `freq_7` | 7 | Tần suất 7 kỳ gần nhất |
| `freq_14` | 14 | Tần suất 14 kỳ |
| `freq_30` | 30 | Tần suất 30 kỳ |
| `freq_60` | 60 | Tần suất 60 kỳ |
| `freq_90` | 90 | Tần suất 90 kỳ |
| `freq_180` | 180 | Tần suất 180 kỳ |
| `freq_365` | 365 | Tần suất 365 kỳ |

**Quy tắc leakage:** Window tính bằng **số kỳ quay thực tế**, không phải số ngày calendar. Query: `draw_date < target_date ORDER BY draw_date DESC LIMIT {window}`.

**Interface:**

```python
def compute_frequency_features(
    number: str,
    target_date: str,
    history: pd.DataFrame,    # columns: [draw_date, loto_number] hoặc [draw_date, special_2d]
    windows: list[int] = [7, 14, 30, 60, 90, 180, 365],
) -> dict[str, int]:
    """Return dict of freq_7, freq_14, ..., freq_365."""
    ...
```

**Biến thể cho target types:**
- `loto_2d`: đếm trong bảng `loto_2digits` (tất cả 27 entries mỗi ngày).
- `db_2d`: đếm trong bảng `targets_db_2d` chỉ nơi `label=1` (1 entry/ngày từ special prize 2D).
- `db_3d`: đếm trong bảng `targets_db_3d` chỉ nơi `label=1` (1 entry/ngày từ special prize 3D).

### 2.2. Gap Features (`gap_features.py`)

| Feature Name | Description |
|:---|:---|
| `current_gap` | Số kỳ liên tiếp number chưa xuất hiện (tính đến kỳ trước `target_date`) |
| `max_gap` | Khoảng gap lớn nhất trong toàn bộ lịch sử |
| `avg_gap` | Gap trung bình trong toàn bộ lịch sử |
| `draws_since_last` | = `current_gap` (alias rõ nghĩa hơn) |

**Interface:**

```python
def compute_gap_features(
    number: str,
    target_date: str,
    history: pd.DataFrame,
) -> dict[str, float]:
    """Return dict with current_gap, max_gap, avg_gap."""
    ...
```

**Xử lý edge case:**
- Number chưa bao giờ xuất hiện: `current_gap = total_draws`, `max_gap = total_draws`, `avg_gap = total_draws`.
- Number xuất hiện ở kỳ ngay trước `target_date`: `current_gap = 0`.

### 2.3. Rolling Features (`rolling_features.py`)

| Feature Name | Description |
|:---|:---|
| `rolling_hits_30` | Tổng số nháy (hits) trong 30 kỳ gần nhất (có thể > freq_30 nếu nổ nhiều nháy) |
| `rolling_hits_60` | Tổng nháy 60 kỳ |
| `avg_hits_per_appearance_30` | Trung bình nháy mỗi lần xuất hiện trong 30 kỳ |
| `hit_streak` | Số kỳ liên tiếp gần nhất mà number xuất hiện (streak hiện tại) |

**Ghi chú:** `rolling_hits` khác `freq` ở chỗ:
- `freq_30` đếm **số kỳ** number xuất hiện (binary per draw: 0 hoặc 1).
- `rolling_hits_30` đếm **tổng số nháy** (có thể 0, 1, 2, 3 nháy mỗi kỳ).
- Sự khác biệt này chỉ có ý nghĩa cho `loto_2d` (vì 27 entries/ngày, 1 số có thể nổ nhiều nháy).
- Cho `db_2d`/`db_3d`: `rolling_hits` = `freq` (vì chỉ có 1 entry/ngày).

### 2.4. Special-Only Features (cho `db_2cang` và `db_3cang`)

Ngoài các features chung, target `db_2d` và `db_3d` cần features riêng tính từ **chỉ giải Đặc biệt**:

| Feature Name | Description |
|:---|:---|
| `special_freq_30` | Số lần giải ĐB 2D/3D trùng number trong 30 kỳ |
| `special_current_gap` | Gap hiện tại tính từ giải ĐB |
| `special_max_gap` | Max gap lịch sử tính từ giải ĐB |

**Lưu ý:** Các features này tính từ series khác (chỉ 1 số/ngày) nên pattern khác với loto_2d (27 số/ngày).

### 2.5. Calendar Features (optional, cẩn thận)

| Feature Name | Description | Cảnh báo |
|:---|:---|:---|
| `day_of_week` | 0=Monday .. 6=Sunday | Có thể noise nếu lottery truly random |
| `day_of_month` | 1..31 | Cẩn trọng overfitting |
| `month` | 1..12 | Cẩn trọng overfitting |

**Quyết định:** Bao gồm `day_of_week` trong MVP. Không bao gồm `day_of_month` và `month` (quá dễ overfit, lottery theory gợi ý independence).

---

## 3. Quy tắc tuyệt đối: No Future Leakage

### 3.1. Rule

> Features cho `(target_date, number)` chỉ được tính từ dữ liệu `draw_date < target_date`.

### 3.2. Implementation Guard

```python
def _validate_no_leakage(feature_dates: list[str], target_date: str) -> None:
    """Assert no feature date is >= target_date."""
    for d in feature_dates:
        assert d < target_date, (
            f"LEAKAGE DETECTED: feature uses date {d} for target_date {target_date}"
        )
```

Gọi hàm này ở **mỗi** feature computation function.

### 3.3. Unit Test Guard

```python
# tests/test_features.py

def test_no_future_leakage():
    """Ensure features for target_date only use data from before target_date."""
    target_date = "2024-06-15"
    features = compute_all_features("42", target_date, history)

    # Verify feature data dates
    used_dates = get_used_dates_from_features(features)
    for d in used_dates:
        assert d < target_date, f"Leakage: used {d} for target {target_date}"
```

---

## 4. Feature Dataset Builder (`build_dataset.py`)

### 4.1. Orchestration

```python
def build_feature_dataset(
    target_type: str,           # 'loto_2d', 'db_2d', 'db_3d'
    start_date: str,
    end_date: str,
    repo: XSMBRepository,
    min_history_days: int = 365,  # minimum history before first target_date
) -> pd.DataFrame:
    """Build complete feature dataset for a target type.

    For each target_date in [start_date, end_date]:
        For each number in number_range:
            Compute all features using data < target_date
            Get label from targets table

    Returns DataFrame with columns:
        [target_date, number, freq_7, freq_14, ..., current_gap, ..., label]
    """
    ...
```

### 4.2. Feature Column List (MVP)

```python
FEATURE_COLUMNS = [
    # Identifiers (not features for model)
    "target_date",
    "number",

    # Frequency features
    "freq_7", "freq_14", "freq_30", "freq_60", "freq_90", "freq_180", "freq_365",

    # Gap features
    "current_gap", "max_gap", "avg_gap",

    # Rolling features
    "rolling_hits_30", "rolling_hits_60", "hit_streak",

    # Calendar
    "day_of_week",

    # Label
    "label",
    "actual_hits",  # chỉ cho loto_2d
]

# Features actually used by model (exclude identifiers + label)
MODEL_FEATURES = [
    "freq_7", "freq_14", "freq_30", "freq_60", "freq_90", "freq_180", "freq_365",
    "current_gap", "max_gap", "avg_gap",
    "rolling_hits_30", "rolling_hits_60", "hit_streak",
    "day_of_week",
]
```

### 4.3. Storage

- Primary: Lưu dạng CSV trong `data/processed/features_{target_type}.csv`.
- Secondary: Có thể insert vào `feature_rows` table (optional cho query).
- Lý do chọn CSV primary: linh hoạt khi thêm/bớt features, dễ inspect bằng pandas.

---

## 5. Performance Plan cho `db_3cang`

- 1000 numbers × N target dates = rất nhiều feature computations.
- **Optimization 1:** Pre-compute daily aggregate (mỗi ngày: số nào xuất hiện trong giải ĐB 3 chữ số cuối) → lookup table O(1).
- **Optimization 2:** Vectorize frequency computation bằng pandas rolling/cumsum thay vì loop từng number.
- **Optimization 3:** Batch process theo chunk dates (ví dụ 30 ngày/batch) để giới hạn memory.

---

## 6. CLI Command

```bash
# Build features cho specific target type
python -m app.main build-features --target loto_2d_all_prizes --start-date 2015-01-01 --end-date 2024-12-31
python -m app.main build-features --target db_2cang --start-date 2015-01-01 --end-date 2024-12-31
python -m app.main build-features --target db_3cang --start-date 2015-01-01 --end-date 2024-12-31
```

Output: CSV files in `data/processed/`.
