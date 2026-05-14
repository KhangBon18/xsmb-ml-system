# 08 — Modeling Plan

---

## 1. Model Taxonomy

### 1.1. Baselines (phải implement trước ML)

| Model | Tên code | Mô tả | Target types |
|:---|:---|:---|:---|
| Random Baseline | `random_baseline` | Gán uniform probability cho mọi số | Cả 3 |
| Frequency Baseline | `freq_baseline` | Xác suất tỷ lệ với tần suất 30 kỳ gần nhất | Cả 3 |
| Gap/Gan Baseline | `gap_baseline` | Xác suất tỷ lệ với current_gap / max_gap | Cả 3 |

### 1.2. ML Models (MVP)

| Model | Tên code | Mô tả | Target types |
|:---|:---|:---|:---|
| Logistic Regression | `logistic` | Linear model, well-calibrated inherently | Cả 3 |
| Hist Gradient Boosting | `hgb` | Tree model, sklearn built-in, fast | Cả 3 |

### 1.3. ML Models (optional, post-MVP)

| Model | Tên code | Dependency |
|:---|:---|:---|
| LightGBM | `lgbm` | `lightgbm` |
| XGBoost | `xgb` | `xgboost` |

---

## 2. Baseline Implementations

### 2.1. Random Baseline

```python
def random_baseline(numbers: list[str], target_type: str) -> list[dict]:
    """Assign uniform probability to all numbers.

    For loto_2d: P ≈ 0.27 (theo lý thuyết: 1 - (73/100)^27 ≈ 0.9997... nhưng
                 thực tế trung bình ~23-25 unique/27 entries → P ≈ 0.24)
    Dùng historical average frequency as uniform P.

    For db_2d: P = 1/100 = 0.01
    For db_3d: P = 1/1000 = 0.001
    """
    ...
```

### 2.2. Frequency Baseline

```python
def frequency_baseline(
    numbers: list[str],
    target_date: str,
    history: pd.DataFrame,
    window: int = 30,
) -> list[dict]:
    """Rank numbers by frequency in last `window` draws.

    P(number) = freq(number, window) / total_appearances_in_window
    Normalize to sum to expected number of hits.
    """
    ...
```

### 2.3. Gap/Gan Baseline

```python
def gap_baseline(
    numbers: list[str],
    target_date: str,
    history: pd.DataFrame,
) -> list[dict]:
    """Rank numbers by how close current_gap is to max_gap.

    Intuition: số nào "quá hạn" (gap gần max) → xác suất cao hơn.
    P(number) ∝ current_gap / max_gap (capped at 1.0).
    """
    ...
```

---

## 3. ML Model Design

### 3.1. Training Interface

```python
# xsmb/models/train.py

def train_model(
    target_type: str,
    model_name: str,           # 'logistic', 'hgb'
    train_df: pd.DataFrame,    # feature dataset
    feature_columns: list[str],
    hyperparams: dict | None = None,
    random_seed: int = 42,
) -> TrainedModel:
    """Train a model and return TrainedModel wrapper.

    Steps:
    1. Extract X (features) and y (labels).
    2. Fit model.
    3. Calibrate if needed (CalibratedClassifierCV).
    4. Return TrainedModel with metadata.
    """
    ...

@dataclass
class TrainedModel:
    model: Any               # sklearn estimator
    model_name: str
    target_type: str
    feature_columns: list[str]
    train_start: str
    train_end: str
    hyperparams: dict
    is_calibrated: bool
```

### 3.2. Default Hyperparameters

```python
DEFAULT_HYPERPARAMS = {
    "logistic": {
        "C": 1.0,
        "max_iter": 1000,
        "solver": "lbfgs",
        "random_state": 42,
    },
    "hgb": {
        "max_iter": 200,
        "max_depth": 5,
        "learning_rate": 0.1,
        "min_samples_leaf": 20,
        "random_state": 42,
    },
}
```

### 3.3. Calibration Plan

- **Logistic Regression:** Inherently well-calibrated. Calibration optional nhưng vẫn check bằng calibration curve.
- **HistGradientBoosting:** **Bắt buộc** wrap bằng `CalibratedClassifierCV(method='isotonic', cv=5)`.
- **Calibration check:** Plot reliability diagram (calibration curve) sau training.

```python
from sklearn.calibration import CalibratedClassifierCV

def calibrate_model(model, X_cal, y_cal, method='isotonic', cv=5):
    """Calibrate a model's probability outputs."""
    cal_model = CalibratedClassifierCV(model, method=method, cv=cv)
    cal_model.fit(X_cal, y_cal)
    return cal_model
```

---

## 4. Model Registry (Local)

### 4.1. Save Model

```python
import joblib
from pathlib import Path

def save_model(trained_model: TrainedModel, repo: XSMBRepository) -> str:
    """Save model to disk and register in DB.

    File: data/models/{target_type}_{model_name}_{run_id}.joblib
    Returns: run_id
    """
    ...
```

### 4.2. Load Model

```python
def load_model(run_id: str, repo: XSMBRepository) -> TrainedModel:
    """Load model from disk using run_id lookup in DB."""
    ...
```

### 4.3. File Naming Convention

```
data/models/
├── loto_2d_logistic_20240115_143022.joblib
├── loto_2d_hgb_20240115_143045.joblib
├── db_2d_logistic_20240115_143100.joblib
├── db_3d_logistic_20240115_143115.joblib
└── ...
```

---

## 5. Prediction Interface

```python
# xsmb/models/predict.py

def predict(
    trained_model: TrainedModel,
    feature_df: pd.DataFrame,    # features cho target_date
    top_k: int | None = None,    # nếu None, trả về tất cả
) -> list[dict]:
    """Generate probability predictions for all numbers.

    Returns list sorted by probability descending:
    [
        {"number": "68", "probability": 0.354, "rank": 1, ...},
        {"number": "86", "probability": 0.312, "rank": 2, ...},
        ...
    ]
    """
    ...
```

---

## 6. Model Output Sizes

| Target Type | Output Size | Probability Range (expected) |
|:---|:---|:---|
| `loto_2d` | 100 items | 0.05 - 0.50 |
| `db_2d` | 100 items | 0.001 - 0.05 |
| `db_3d` | 1000 items | 0.0001 - 0.01 |

---

## 7. Handling Class Imbalance

### 7.1. `loto_2d` — Mild imbalance
- ~24% positive rate → không cần xử lý đặc biệt.

### 7.2. `db_2d` — Moderate imbalance (1:99)
- Logistic Regression: set `class_weight='balanced'`.
- HGB: set `class_weight='balanced'` hoặc custom sample weights.

### 7.3. `db_3d` — Extreme imbalance (1:999)
- **Strategy 1:** `class_weight='balanced'` (scale automatically).
- **Strategy 2:** Evaluate bằng ranking metrics (P@K, Recall@K) thay vì accuracy.
- **Strategy 3 (post-MVP):** Undersampling negatives kết hợp ensemble.
- **Ghi chú:** Brier Score cho db_3d sẽ rất thấp (good) ngay cả khi predict 0.001 cho mọi số. Cần dùng Brier Skill Score (so với baseline) để đánh giá đúng.

---

## 8. KHÔNG ĐƯỢC HỨA

> Hệ thống này chỉ tạo **ranking xác suất dựa trên patterns lịch sử**. Lottery numbers về bản chất là random. Model ML có thể tìm được weak patterns nhưng KHÔNG THỂ dự đoán chính xác. Mọi đánh giá phải dựa trên backtest nghiêm ngặt và so sánh với random baseline.
