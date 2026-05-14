# 04 — Database Schema Plan

---

## 1. Database Engine: SQLite (MVP)

- **Lý do:** AGENTS.md yêu cầu SQLite cho MVP. Lightweight, zero-config, portable.
- **File path:** `data/xsmb.db`
- **Driver:** Python stdlib `sqlite3` (không cần SQLAlchemy cho MVP).
- **Migration path:** Có thể chuyển PostgreSQL sau MVP bằng cách abstract repository layer.

---

## 2. Schema DDL hoàn chỉnh

```sql
-- =============================================================
-- XSMB ML System — SQLite Schema
-- Version: 2.0
-- =============================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ----- 1. RAW STORAGE -----
CREATE TABLE IF NOT EXISTS raw_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT    NOT NULL,
    source_name TEXT    NOT NULL,
    source_url  TEXT    NOT NULL,
    raw_content TEXT    NOT NULL,
    crawled_at  TEXT    NOT NULL,
    UNIQUE(draw_date, source_name)
);

-- ----- 2. PARSED RESULTS -----
CREATE TABLE IF NOT EXISTS draw_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date       TEXT    NOT NULL,
    prize_tier      TEXT    NOT NULL CHECK(prize_tier IN (
        'special','first','second','third','fourth','fifth','sixth','seventh'
    )),
    prize_index     INTEGER NOT NULL CHECK(prize_index >= 0),
    winning_number  TEXT    NOT NULL,
    UNIQUE(draw_date, prize_tier, prize_index)
);
CREATE INDEX IF NOT EXISTS idx_draw_results_date ON draw_results(draw_date);

-- ----- 3. LOTO 2 DIGITS -----
CREATE TABLE IF NOT EXISTS loto_2digits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT    NOT NULL,
    prize_tier  TEXT    NOT NULL,
    prize_index INTEGER NOT NULL,
    loto_number TEXT    NOT NULL CHECK(length(loto_number) = 2),
    UNIQUE(draw_date, prize_tier, prize_index)
);
CREATE INDEX IF NOT EXISTS idx_loto_2d_date   ON loto_2digits(draw_date);
CREATE INDEX IF NOT EXISTS idx_loto_2d_number ON loto_2digits(loto_number);

-- ----- 4. TARGET: LOTO 2D ALL PRIZES -----
CREATE TABLE IF NOT EXISTS targets_loto_2d (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT    NOT NULL,
    number      TEXT    NOT NULL CHECK(length(number) = 2),
    label       INTEGER NOT NULL CHECK(label IN (0, 1)),
    actual_hits INTEGER NOT NULL CHECK(actual_hits >= 0),
    UNIQUE(draw_date, number)
);
CREATE INDEX IF NOT EXISTS idx_targets_loto_2d_date ON targets_loto_2d(draw_date);

-- ----- 5. TARGET: DB 2 CÀNG -----
CREATE TABLE IF NOT EXISTS targets_db_2d (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT    NOT NULL,
    number      TEXT    NOT NULL CHECK(length(number) = 2),
    label       INTEGER NOT NULL CHECK(label IN (0, 1)),
    UNIQUE(draw_date, number)
);
CREATE INDEX IF NOT EXISTS idx_targets_db_2d_date ON targets_db_2d(draw_date);

-- ----- 6. TARGET: DB 3 CÀNG -----
CREATE TABLE IF NOT EXISTS targets_db_3d (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT    NOT NULL,
    number      TEXT    NOT NULL CHECK(length(number) = 3),
    label       INTEGER NOT NULL CHECK(label IN (0, 1)),
    UNIQUE(draw_date, number)
);
CREATE INDEX IF NOT EXISTS idx_targets_db_3d_date ON targets_db_3d(draw_date);

-- ----- 7. MODEL REGISTRY -----
CREATE TABLE IF NOT EXISTS model_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    NOT NULL UNIQUE,
    model_name  TEXT    NOT NULL,
    target_type TEXT    NOT NULL CHECK(target_type IN ('loto_2d','db_2d','db_3d')),
    train_start TEXT    NOT NULL,
    train_end   TEXT    NOT NULL,
    hyperparams TEXT,
    model_path  TEXT,
    created_at  TEXT    NOT NULL
);

-- ----- 8. PREDICTIONS -----
CREATE TABLE IF NOT EXISTS predictions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT    NOT NULL,
    predict_date TEXT   NOT NULL,
    number      TEXT    NOT NULL,
    probability REAL    NOT NULL CHECK(probability >= 0 AND probability <= 1),
    rank        INTEGER NOT NULL CHECK(rank >= 1),
    UNIQUE(run_id, predict_date, number),
    FOREIGN KEY (run_id) REFERENCES model_runs(run_id)
);
CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(predict_date);

-- ----- 9. BACKTEST RUNS -----
CREATE TABLE IF NOT EXISTS backtest_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id     TEXT    NOT NULL UNIQUE,
    run_id          TEXT    NOT NULL,
    target_type     TEXT    NOT NULL,
    bt_start_date   TEXT    NOT NULL,
    bt_end_date     TEXT    NOT NULL,
    window_type     TEXT    NOT NULL CHECK(window_type IN ('expanding','sliding')),
    retrain_freq    TEXT    NOT NULL CHECK(retrain_freq IN ('daily','weekly','monthly')),
    created_at      TEXT    NOT NULL,
    FOREIGN KEY (run_id) REFERENCES model_runs(run_id)
);

-- ----- 10. BACKTEST PREDICTIONS -----
CREATE TABLE IF NOT EXISTS backtest_predictions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    backtest_id     TEXT    NOT NULL,
    backtest_date   TEXT    NOT NULL,
    number          TEXT    NOT NULL,
    predicted_prob  REAL    NOT NULL,
    actual_label    INTEGER NOT NULL,
    actual_hits     INTEGER DEFAULT 0,
    UNIQUE(backtest_id, backtest_date, number),
    FOREIGN KEY (backtest_id) REFERENCES backtest_runs(backtest_id)
);
CREATE INDEX IF NOT EXISTS idx_bt_preds ON backtest_predictions(backtest_id, backtest_date);
```

---

## 3. Constraints & Invariants

| Bảng | Constraint | Mô tả |
|:---|:---|:---|
| `raw_results` | `UNIQUE(draw_date, source_name)` | Mỗi ngày chỉ crawl 1 lần từ mỗi source |
| `draw_results` | `UNIQUE(draw_date, prize_tier, prize_index)` | Không duplicate giải |
| `draw_results` | Application-level: count=27/date | Validate trước INSERT |
| `loto_2digits` | `CHECK(length(loto_number) = 2)` | Luôn 2 ký tự |
| `targets_loto_2d` | Application: 100 rows/date, sum(label)=~23-25 | Validate post-insert |
| `targets_db_2d` | Application: 100 rows/date, sum(label)=1 | Validate post-insert |
| `targets_db_3d` | Application: 1000 rows/date, sum(label)=1 | Validate post-insert |
| `predictions` | `CHECK(probability >= 0 AND <= 1)` | Xác suất hợp lệ |

---

## 4. Performance Considerations

### 4.1. `targets_db_3d` — Bảng lớn nhất

- 1000 rows/date × 3650 days (10 năm) = **3,650,000 rows**.
- Index trên `draw_date` là bắt buộc.
- Insert nên dùng batch `executemany()` với transaction.
- Query pattern chính: `WHERE draw_date BETWEEN ? AND ?` → covered by index.

### 4.2. `backtest_predictions` — Có thể lớn

- Nếu backtest 1 năm cho `db_3cang`: 365 × 1000 = 365,000 rows per backtest run.
- Cân nhắc chỉ lưu top-K predictions thay vì full 1000 nếu quá lớn.
- Alternative: export trực tiếp ra CSV, không lưu DB.

### 4.3. WAL mode

- `PRAGMA journal_mode = WAL` cho phép concurrent reads khi CLI và analysis tool đều truy cập DB.

---

## 5. DB Connection Design

```python
# xsmb/database/connection.py

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data/xsmb.db")

def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create or open SQLite connection with safety pragmas."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # dict-like access
    return conn

def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Initialize database schema from schema.sql."""
    schema_path = Path(__file__).parent / "schema.sql"
    conn = get_connection(db_path)
    with open(schema_path) as f:
        conn.executescript(f.read())
    conn.close()
```

---

## 6. Repository Pattern Design

```python
# xsmb/database/repository.py — Interface methods

class XSMBRepository:
    """Data access layer for XSMB database."""

    def __init__(self, conn: sqlite3.Connection): ...

    # Raw results
    def upsert_raw_result(self, draw_date, source_name, source_url, raw_content) -> None: ...
    def get_raw_result(self, draw_date, source_name) -> Optional[dict]: ...
    def get_raw_dates_range(self, start_date, end_date) -> list[str]: ...

    # Draw results
    def insert_draw_results(self, draw_date, prizes: list[dict]) -> None: ...
    def get_draw_results(self, draw_date) -> list[dict]: ...
    def get_dates_with_results(self) -> list[str]: ...

    # Loto 2digits
    def insert_loto_2digits(self, draw_date, entries: list[dict]) -> None: ...
    def get_loto_2digits(self, draw_date) -> list[dict]: ...
    def get_loto_2digits_range(self, start_date, end_date) -> list[dict]: ...

    # Targets
    def insert_targets_loto_2d(self, draw_date, rows: list[dict]) -> None: ...
    def insert_targets_db_2d(self, draw_date, rows: list[dict]) -> None: ...
    def insert_targets_db_3d(self, draw_date, rows: list[dict]) -> None: ...

    # Model runs
    def insert_model_run(self, run: dict) -> None: ...
    def get_model_run(self, run_id) -> Optional[dict]: ...

    # Predictions
    def insert_predictions(self, run_id, predict_date, predictions: list[dict]) -> None: ...

    # Backtest
    def insert_backtest_run(self, bt: dict) -> None: ...
    def insert_backtest_predictions(self, backtest_id, predictions: list[dict]) -> None: ...
```
