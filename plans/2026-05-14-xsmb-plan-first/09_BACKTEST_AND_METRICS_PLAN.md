# 09 — Backtest and Metrics Plan

---

## 1. Backtest Strategy: Walk-Forward Validation

### 1.1. Overview

```
Time ──────────────────────────────────────────────────────►

[==========TRAIN==========][TEST]
                            t=1

[===========TRAIN===========][TEST]
                              t=2

[============TRAIN============][TEST]
                                t=3
...
```

- **Window type (MVP):** Expanding window (tất cả data từ đầu đến t-1).
- **Sliding window (optional):** Cố định size, bỏ data cũ nhất khi thêm data mới.
- **KHÔNG dùng random split.**

### 1.2. Parameters

| Parameter | Default (MVP) | Configurable |
|:---|:---|:---|
| `window_type` | `expanding` | Có |
| `retrain_frequency` | `monthly` | Có (`daily`, `weekly`, `monthly`) |
| `min_train_days` | 365 (1 năm) | Có |
| `test_step` | 1 ngày | Cố định |
| `initial_train_end` | Từ `start_date` + `min_train_days` | Tự tính |

### 1.3. Retrain Frequency

- `daily`: Train lại model **mỗi ngày** → chính xác nhất nhưng chậm nhất.
- `weekly`: Train lại **mỗi tuần** → trade-off tốt.
- `monthly`: Train lại **mỗi tháng** → nhanh nhất cho MVP.

MVP dùng `monthly` để tiết kiệm thời gian. Khi chạy 1 năm backtest:
- `daily`: ~365 lần train.
- `monthly`: ~12 lần train, dùng model cùng tháng cho 30 ngày liên tiếp.

---

## 2. Backtest Engine

### 2.1. Interface

```python
# xsmb/models/backtest.py

def run_backtest(
    target_type: str,
    model_name: str,
    bt_start_date: str,
    bt_end_date: str,
    feature_df: pd.DataFrame,
    feature_columns: list[str],
    window_type: str = "expanding",
    retrain_freq: str = "monthly",
    min_train_days: int = 365,
    random_seed: int = 42,
) -> BacktestResult:
    """Run walk-forward backtest.

    Algorithm:
    1. Get sorted list of target_dates in [bt_start_date, bt_end_date].
    2. For each target_date t:
       a. If retrain needed (first run or frequency trigger):
          - train_data = feature_df[feature_df.target_date < t]
          - model = train_model(target_type, model_name, train_data, ...)
       b. test_data = feature_df[feature_df.target_date == t]
       c. predictions = predict(model, test_data)
       d. Store predictions + actual labels
    3. Compute metrics across all test dates.
    4. Return BacktestResult.
    """
    ...
```

### 2.2. Anti-Leakage Safeguards

```python
def _assert_train_before_test(train_dates, test_date):
    """Assert all training dates are strictly before test date."""
    max_train = max(train_dates)
    assert max_train < test_date, (
        f"LEAKAGE: max train date {max_train} >= test date {test_date}"
    )

def _assert_scaler_fit_on_train(scaler, fitted_on_dates, test_date):
    """Assert scaler was fit only on training data."""
    ...
```

### 2.3. Scaler Handling

- **Rule:** Scaler (nếu dùng StandardScaler/MinMaxScaler) phải `fit()` chỉ trên train data.
- **MVP approach:** Không dùng scaler cho Logistic Regression (dùng raw features). HGB không cần scaling.
- **Nếu cần scaler:** Re-fit mỗi lần retrain, chỉ trên train data tại thời điểm đó.

---

## 3. Metrics (cho mỗi target type)

### 3.1. Metrics per day

| Metric | Mô tả | Áp dụng |
|:---|:---|:---|
| `brier_score` | Mean squared error giữa P(y) và actual y | Cả 3 |
| `log_loss` | Cross-entropy loss | Cả 3 |
| `precision_at_k` | Precision trong top-K predictions | Cả 3 |
| `recall_at_k` | Recall trong top-K predictions | Cả 3 |
| `hit_rate_at_k` | P(≥1 hit trong top-K) | Cả 3 |
| `avg_hits_at_k` | Trung bình số hits trong top-K | Chủ yếu loto_2d |

### 3.2. Metric Definitions

```python
def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Mean squared error between probabilities and binary labels."""
    return np.mean((y_prob - y_true) ** 2)

def precision_at_k(y_true: np.ndarray, y_prob: np.ndarray, k: int) -> float:
    """Precision among top-K highest probability predictions."""
    top_k_idx = np.argsort(y_prob)[-k:]
    return np.mean(y_true[top_k_idx])

def hit_rate_at_k(y_true: np.ndarray, y_prob: np.ndarray, k: int) -> float:
    """1 if at least one hit in top-K, else 0."""
    top_k_idx = np.argsort(y_prob)[-k:]
    return float(np.any(y_true[top_k_idx] == 1))

def avg_hits_at_k(y_true: np.ndarray, y_prob: np.ndarray, k: int, actual_hits: np.ndarray = None) -> float:
    """Average number of actual hits in top-K (counts multi-hits for loto_2d)."""
    top_k_idx = np.argsort(y_prob)[-k:]
    if actual_hits is not None:
        return np.mean(actual_hits[top_k_idx])
    return np.sum(y_true[top_k_idx])
```

### 3.3. K values per target type

| Target Type | K values | Rationale |
|:---|:---|:---|
| `loto_2d` | 5, 10, 15, 20 | Người chơi thường chọn 5-20 số |
| `db_2d` | 1, 3, 5, 10 | Đề 2 càng thường chọn 1-10 số |
| `db_3d` | 1, 5, 10, 20 | Đề 3 càng, 1/1000 → cần K lớn hơn |

---

## 4. Special Considerations per Target

### 4.1. `loto_2d_all_prizes`

- Baseline performance: Random P@10 ≈ 0.24, Hit@5 ≈ 0.75.
- Brier Score baseline: ~0.18 (vì P(hit) ≈ 0.24).
- `avg_hits@K` có ý nghĩa vì loto có nhiều nháy.

### 4.2. `db_2cang`

- Baseline performance: Random P@1 = 0.01 (1%), P@5 = 0.05 (5%).
- Hit@10 baseline ≈ 0.10 (10%).
- Brier Score baseline ≈ 0.0099 (rất thấp do class imbalance).
- **Cần dùng Brier Skill Score** = 1 - BS_model / BS_baseline.

### 4.3. `db_3cang`

- **CỰC KỲ khó.** Random P@1 = 0.001 (0.1%).
- Hit@10 baseline = 0.01 (1%).
- Brier Score baseline ≈ 0.000999 → gần 0 → vô nghĩa nếu nhìn raw score.
- **Bắt buộc:** So sánh với random baseline bằng relative improvement.
- **Kỳ vọng thực tế:** ML model có thể KHÔNG đánh bại frequency baseline cho db_3cang. Điều này phải được ghi nhận trung thực.

---

## 5. Calibration Evaluation

### 5.1. Reliability Table

Chia predictions thành bins (ví dụ: 10 bins từ 0.0 đến 1.0):

```
Bin [0.0-0.1]:  predicted_avg=0.05,  actual_rate=0.04  → OK
Bin [0.1-0.2]:  predicted_avg=0.15,  actual_rate=0.17  → OK
Bin [0.2-0.3]:  predicted_avg=0.25,  actual_rate=0.23  → OK
...
```

### 5.2. Calibration Curve

Plot predicted probability vs actual frequency → should be close to diagonal.

---

## 6. Report Formats

### 6.1. Raw Predictions CSV

File: `data/reports/backtest_raw_{target}_{model}_{timestamp}.csv`

```csv
backtest_date,model_name,target_type,number,predicted_prob,rank,actual_label,actual_hits
2024-01-16,logistic,loto_2d,68,0.354,1,1,1
2024-01-16,logistic,loto_2d,86,0.312,2,0,0
```

### 6.2. Daily Summary CSV

File: `data/reports/backtest_summary_{target}_{model}_{timestamp}.csv`

```csv
backtest_date,model_name,target_type,brier_score,log_loss,precision_at_5,precision_at_10,hit_rate_at_5,hit_rate_at_10,avg_hits_at_5,avg_hits_at_10
2024-01-16,logistic,loto_2d,0.185,0.512,0.40,0.30,1.0,1.0,2.0,3.0
```

### 6.3. Overall Summary (aggregated)

File: `data/reports/backtest_overall_{target}_{model}_{timestamp}.csv`

```csv
model_name,target_type,bt_start_date,bt_end_date,num_days,avg_brier,avg_log_loss,avg_p_at_5,avg_p_at_10,avg_hit_at_5,avg_hit_at_10,avg_hits_at_5,avg_hits_at_10
logistic,loto_2d,2024-01-01,2024-12-31,365,0.182,0.498,0.32,0.28,0.95,0.99,1.8,2.9
random_baseline,loto_2d,2024-01-01,2024-12-31,365,0.188,0.520,0.24,0.24,0.75,0.92,1.2,2.4
```

---

## 7. Baseline Comparison Rule

> Một mô hình ML chỉ được coi là "hữu ích" nếu:
> 1. `Brier Score` thấp hơn random baseline.
> 2. `Precision@K` hoặc `Hit_rate@K` cao hơn random baseline **VÀ** frequency baseline.
> 3. Sự khác biệt phải **nhất quán** qua nhiều tháng (không chỉ 1-2 ngày).
>
> Nếu ML model không đánh bại baselines → sử dụng baseline tốt nhất, loại bỏ ML model phức tạp.

---

## 8. CLI Commands

```bash
# Backtest cho loto_2d với logistic model
python -m app.main backtest --target loto_2d_all_prizes --model logistic --start-date 2024-01-01 --end-date 2024-12-31

# Backtest cho db_2cang
python -m app.main backtest --target db_2cang --model logistic --start-date 2024-01-01 --end-date 2024-12-31

# Backtest cho db_3cang
python -m app.main backtest --target db_3cang --model logistic --start-date 2024-01-01 --end-date 2024-12-31

# So sánh tất cả models cho 1 target
python -m app.main backtest --target loto_2d_all_prizes --model all --start-date 2024-01-01 --end-date 2024-12-31
```
