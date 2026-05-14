# 03 — Data Contract V2

Bản V2 bổ sung `db_2cang`, `db_3cang`, model registry, và backtest storage. Giữ nguyên tinh thần DATA_CONTRACT.md gốc.

---

## 1. Quy tắc kiểu dữ liệu (Type Rules)

| Loại dữ liệu | Type (DB) | Type (Python) | Ghi chú |
|:---|:---|:---|:---|
| Số xổ số (winning_number) | `TEXT` | `str` | KHÔNG BAO GIỜ dùng INT |
| Số loto (loto_number) | `TEXT` | `str` | Luôn 2 ký tự: "00".."99" |
| Số 3 càng (target_number_3d) | `TEXT` | `str` | Luôn 3 ký tự: "000".."999" |
| Ngày | `TEXT` | `str` | ISO YYYY-MM-DD |
| Xác suất | `REAL` | `float` | Trong [0.0, 1.0] |
| Model version | `TEXT` | `str` | Format: `{model_name}_v{version}` |
| Run ID | `TEXT` | `str` | UUID hoặc timestamp-based |
| Counts | `INTEGER` | `int` | ≥ 0 |
| Boolean label | `INTEGER` | `int` | 0 hoặc 1 |

---

## 2. Schema Logic cho từng bảng

### 2.1. `raw_results` — Lưu trữ thô (raw HTML)

```sql
CREATE TABLE raw_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT NOT NULL,          -- YYYY-MM-DD
    source_name TEXT NOT NULL,          -- tên adapter source
    source_url  TEXT NOT NULL,          -- URL đã crawl
    raw_content TEXT NOT NULL,          -- HTML/JSON thô
    crawled_at  TEXT NOT NULL,          -- ISO timestamp
    UNIQUE(draw_date, source_name)
);
```

**Ghi chú:**
- `UNIQUE(draw_date, source_name)` → idempotent crawl.
- `raw_content` là toàn bộ response body (HTML hoặc JSON tùy source).
- Dùng để re-parse khi parser thay đổi.

### 2.2. `draw_results` — Kết quả đầy đủ (parsed)

```sql
CREATE TABLE draw_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date       TEXT NOT NULL,
    prize_tier      TEXT NOT NULL,      -- special, first, second, ..., seventh
    prize_index     INTEGER NOT NULL,   -- 0-indexed trong cùng tier
    winning_number  TEXT NOT NULL,      -- giữ leading zeros
    UNIQUE(draw_date, prize_tier, prize_index)
);

CREATE INDEX idx_draw_results_date ON draw_results(draw_date);
```

**Validation khi INSERT:**
- Tổng rows cho 1 `draw_date` phải = 27.
- `len(winning_number)` phải match `PRIZE_STRUCTURE[prize_tier]["digits"]`.
- `winning_number.isdigit()` phải = True.

### 2.3. `loto_2digits` — Loto 2 chữ số (extracted)

```sql
CREATE TABLE loto_2digits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT NOT NULL,
    prize_tier  TEXT NOT NULL,
    prize_index INTEGER NOT NULL,
    loto_number TEXT NOT NULL,          -- luôn 2 ký tự
    UNIQUE(draw_date, prize_tier, prize_index)
);

CREATE INDEX idx_loto_2digits_date ON loto_2digits(draw_date);
CREATE INDEX idx_loto_2digits_number ON loto_2digits(loto_number);
```

### 2.4. `targets_loto_2d` — Target dataset cho loto 2D

```sql
CREATE TABLE targets_loto_2d (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT NOT NULL,
    number      TEXT NOT NULL,          -- "00".."99"
    label       INTEGER NOT NULL,       -- 0 or 1
    actual_hits INTEGER NOT NULL,       -- 0, 1, 2, 3, ...
    UNIQUE(draw_date, number)
);

CREATE INDEX idx_targets_loto_2d_date ON targets_loto_2d(draw_date);
```

**Invariant:** Mỗi `draw_date` phải có **chính xác 100 rows** (1 row cho mỗi "00".."99").

### 2.5. `targets_db_2d` — Target dataset cho đề 2 càng

```sql
CREATE TABLE targets_db_2d (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT NOT NULL,
    number      TEXT NOT NULL,          -- "00".."99"
    label       INTEGER NOT NULL,       -- 0 or 1 (chỉ 1 row = 1)
    UNIQUE(draw_date, number)
);

CREATE INDEX idx_targets_db_2d_date ON targets_db_2d(draw_date);
```

**Invariant:** Mỗi `draw_date` phải có **chính xác 100 rows**, trong đó **đúng 1 row** có `label=1`.

### 2.6. `targets_db_3d` — Target dataset cho đề 3 càng

```sql
CREATE TABLE targets_db_3d (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT NOT NULL,
    number      TEXT NOT NULL,          -- "000".."999"
    label       INTEGER NOT NULL,       -- 0 or 1 (chỉ 1 row = 1)
    UNIQUE(draw_date, number)
);

CREATE INDEX idx_targets_db_3d_date ON targets_db_3d(draw_date);
```

**Invariant:** Mỗi `draw_date` phải có **chính xác 1000 rows**, trong đó **đúng 1 row** có `label=1`.

**Ghi chú hiệu năng:** Bảng này sẽ lớn (~3.65M rows cho 10 năm). Cân nhắc batch insert + index optimization.

### 2.7. `feature_rows` — Feature dataset

```sql
CREATE TABLE feature_rows (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type     TEXT NOT NULL,      -- 'loto_2d', 'db_2d', 'db_3d'
    target_date     TEXT NOT NULL,
    number          TEXT NOT NULL,
    -- Feature columns (dynamic, thêm dần)
    freq_7          INTEGER,
    freq_14         INTEGER,
    freq_30         INTEGER,
    freq_60         INTEGER,
    freq_90         INTEGER,
    freq_180        INTEGER,
    freq_365        INTEGER,
    current_gap     INTEGER,
    max_gap         INTEGER,
    avg_gap         REAL,
    draws_since_last INTEGER,
    rolling_hits_30 INTEGER,
    -- Label
    label           INTEGER NOT NULL,
    UNIQUE(target_type, target_date, number)
);

CREATE INDEX idx_feature_rows_type_date ON feature_rows(target_type, target_date);
```

**Lưu ý:** Schema `feature_rows` sẽ mở rộng khi thêm features mới. Approach thay thế: lưu features dạng CSV/Parquet trong `data/processed/` thay vì DB. Quyết định trong implementation.

### 2.8. `model_runs` — Model Registry

```sql
CREATE TABLE model_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL UNIQUE,
    model_name      TEXT NOT NULL,      -- 'random_baseline', 'freq_baseline', 'logistic', 'rf'
    target_type     TEXT NOT NULL,      -- 'loto_2d', 'db_2d', 'db_3d'
    train_start     TEXT NOT NULL,      -- training data start date
    train_end       TEXT NOT NULL,      -- training data end date
    hyperparams     TEXT,               -- JSON string
    model_path      TEXT,               -- path to saved model file
    created_at      TEXT NOT NULL       -- ISO timestamp
);
```

### 2.9. `predictions` — Prediction Output

```sql
CREATE TABLE predictions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT NOT NULL,
    predict_date    TEXT NOT NULL,
    number          TEXT NOT NULL,
    probability     REAL NOT NULL,
    rank            INTEGER NOT NULL,   -- 1 = highest probability
    UNIQUE(run_id, predict_date, number),
    FOREIGN KEY (run_id) REFERENCES model_runs(run_id)
);

CREATE INDEX idx_predictions_date ON predictions(predict_date);
```

### 2.10. `backtest_runs` — Backtest Metadata

```sql
CREATE TABLE backtest_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id     TEXT NOT NULL UNIQUE,
    run_id          TEXT NOT NULL,      -- model run being backtested
    target_type     TEXT NOT NULL,
    bt_start_date   TEXT NOT NULL,
    bt_end_date     TEXT NOT NULL,
    window_type     TEXT NOT NULL,      -- 'expanding' or 'sliding'
    retrain_freq    TEXT NOT NULL,      -- 'daily', 'weekly', 'monthly'
    created_at      TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES model_runs(run_id)
);
```

### 2.11. `backtest_predictions` — Backtest Detail

```sql
CREATE TABLE backtest_predictions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id     TEXT NOT NULL,
    backtest_date   TEXT NOT NULL,
    number          TEXT NOT NULL,
    predicted_prob  REAL NOT NULL,
    actual_label    INTEGER NOT NULL,
    actual_hits     INTEGER DEFAULT 0,  -- chỉ có ý nghĩa cho loto_2d
    UNIQUE(backtest_id, backtest_date, number),
    FOREIGN KEY (backtest_id) REFERENCES backtest_runs(backtest_id)
);

CREATE INDEX idx_bt_preds_date ON backtest_predictions(backtest_id, backtest_date);
```

---

## 3. Output Prediction Format

### 3.1. `loto_2d_all_prizes` output (100 items)

```json
{
  "predict_date": "2024-01-16",
  "target_type": "loto_2d_all_prizes",
  "model_name": "logistic_v1",
  "predictions": [
    {"number": "68", "probability": 0.354, "rank": 1, "current_gap": 15, "freq_30": 2},
    {"number": "86", "probability": 0.312, "rank": 2, "current_gap": 4, "freq_30": 8},
    ...
  ]
}
```

### 3.2. `db_2cang` output (100 items)

```json
{
  "predict_date": "2024-01-16",
  "target_type": "db_2cang",
  "model_name": "logistic_v1",
  "predictions": [
    {"number": "78", "probability": 0.028, "rank": 1},
    {"number": "45", "probability": 0.025, "rank": 2},
    ...
  ]
}
```

### 3.3. `db_3cang` output (1000 items)

```json
{
  "predict_date": "2024-01-16",
  "target_type": "db_3cang",
  "model_name": "logistic_v1",
  "predictions": [
    {"number": "678", "probability": 0.0042, "rank": 1},
    {"number": "123", "probability": 0.0038, "rank": 2},
    ...
  ]
}
```

---

## 4. Backtest Report Formats

### 4.1. Raw detail CSV: `backtest_raw_{target}_{model}_{timestamp}.csv`

```csv
backtest_date,model_name,target_type,number,predicted_prob,rank,actual_label,actual_hits
2024-01-16,logistic_v1,loto_2d,68,0.354,1,1,1
2024-01-16,logistic_v1,loto_2d,86,0.312,2,0,0
```

### 4.2. Summary CSV: `backtest_summary_{target}_{model}_{timestamp}.csv`

```csv
backtest_date,model_name,target_type,brier_score,log_loss,precision_at_5,precision_at_10,hit_rate_at_5,hit_rate_at_10,avg_hits_at_5,avg_hits_at_10
2024-01-16,logistic_v1,loto_2d,0.185,0.512,0.40,0.30,1.0,1.0,2.0,3.0
```

---

## 5. Migration Note từ DATA_CONTRACT.md V1

| Thay đổi | V1 | V2 |
|:---|:---|:---|
| Database | PostgreSQL (ngầm hiểu) | SQLite (MVP explicit) |
| Target tables | Không có | 3 bảng: `targets_loto_2d`, `targets_db_2d`, `targets_db_3d` |
| Feature storage | Không có | `feature_rows` table hoặc CSV |
| Model registry | Không có | `model_runs` table |
| Prediction storage | Không có | `predictions` table |
| Backtest storage | Không có (chỉ nói CSV) | `backtest_runs` + `backtest_predictions` + CSV export |
| Source tracking | `source_url` | `source_name` + `source_url` (adapter pattern) |
