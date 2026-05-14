# 10 — CLI, API, and Dashboard Plan

---

## 1. Thứ tự ưu tiên

```
CLI (Phase 9) → API (Phase 10a) → Dashboard (Phase 10b)
```

**KHÔNG** triển khai API/Dashboard trước khi CLI + backtest chạy ổn.

---

## 2. CLI Design (`app/main.py`)

### 2.1. Framework: `argparse` (stdlib)

Không thêm dependency (Click, Typer) cho MVP. `argparse` đủ dùng.

### 2.2. Command List

```bash
# ── Data Acquisition ──
python -m app.main scrape --start-date YYYY-MM-DD --end-date YYYY-MM-DD [--force] [--source xoso_com_vn]
python -m app.main reparse --start-date YYYY-MM-DD --end-date YYYY-MM-DD

# ── Processing ──
python -m app.main process --start-date YYYY-MM-DD --end-date YYYY-MM-DD

# ── Target Building ──
python -m app.main build-targets --start-date YYYY-MM-DD --end-date YYYY-MM-DD --target {loto_2d_all_prizes|db_2cang|db_3cang|all}

# ── Feature Engineering ──
python -m app.main build-features --target {loto_2d_all_prizes|db_2cang|db_3cang} --start-date YYYY-MM-DD --end-date YYYY-MM-DD

# ── Training ──
python -m app.main train --target {loto_2d_all_prizes|db_2cang|db_3cang} --model {logistic|hgb|all} [--train-end YYYY-MM-DD]

# ── Backtesting ──
python -m app.main backtest --target {loto_2d_all_prizes|db_2cang|db_3cang} --model {logistic|hgb|random_baseline|freq_baseline|gap_baseline|all} --start-date YYYY-MM-DD --end-date YYYY-MM-DD [--retrain-freq {daily|weekly|monthly}]

# ── Prediction ──
python -m app.main predict --target {loto_2d_all_prizes|db_2cang|db_3cang} --date YYYY-MM-DD [--model logistic] [--top-k 20]

# ── Database ──
python -m app.main init-db
python -m app.main db-status
```

### 2.3. CLI Architecture

```python
# app/main.py

import argparse
import sys

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="xsmb-ml",
        description="XSMB ML System — Statistical analysis and probability ranking"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # scrape
    p_scrape = subparsers.add_parser("scrape", help="Crawl XSMB results")
    p_scrape.add_argument("--start-date", required=True)
    p_scrape.add_argument("--end-date", required=True)
    p_scrape.add_argument("--force", action="store_true")
    p_scrape.add_argument("--source", default="xoso_com_vn")

    # process
    p_process = subparsers.add_parser("process", help="Parse and validate raw results")
    p_process.add_argument("--start-date", required=True)
    p_process.add_argument("--end-date", required=True)

    # build-features
    p_features = subparsers.add_parser("build-features", help="Build feature dataset")
    p_features.add_argument("--target", required=True, choices=["loto_2d_all_prizes","db_2cang","db_3cang"])
    p_features.add_argument("--start-date", required=True)
    p_features.add_argument("--end-date", required=True)

    # train
    p_train = subparsers.add_parser("train", help="Train model")
    p_train.add_argument("--target", required=True)
    p_train.add_argument("--model", required=True)
    p_train.add_argument("--train-end", default=None)

    # backtest
    p_backtest = subparsers.add_parser("backtest", help="Run walk-forward backtest")
    p_backtest.add_argument("--target", required=True)
    p_backtest.add_argument("--model", required=True)
    p_backtest.add_argument("--start-date", required=True)
    p_backtest.add_argument("--end-date", required=True)
    p_backtest.add_argument("--retrain-freq", default="monthly")

    # predict
    p_predict = subparsers.add_parser("predict", help="Generate probability ranking")
    p_predict.add_argument("--target", required=True)
    p_predict.add_argument("--date", required=True)
    p_predict.add_argument("--model", default="logistic")
    p_predict.add_argument("--top-k", type=int, default=20)

    # init-db
    subparsers.add_parser("init-db", help="Initialize database schema")

    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Dispatch to command handlers
    handlers = {
        "scrape": handle_scrape,
        "reparse": handle_reparse,
        "process": handle_process,
        "build-features": handle_build_features,
        "train": handle_train,
        "backtest": handle_backtest,
        "predict": handle_predict,
        "init-db": handle_init_db,
    }
    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
```

### 2.4. Output Format (CLI)

Prediction CLI output example:

```
═══════════════════════════════════════════════
  XSMB Prediction — loto_2d_all_prizes
  Date: 2024-01-16 | Model: logistic_v1
  Top 20 numbers by probability
═══════════════════════════════════════════════
  Rank  Number  Probability  Gap   Freq30
  ────  ──────  ───────────  ───   ──────
   1    68      0.354        15    2
   2    86      0.312         4    8
   3    15      0.298         3    6
   ...
  20    42      0.195        12    3
═══════════════════════════════════════════════
  ⚠️  This is statistical analysis only.
  No prediction accuracy is guaranteed.
═══════════════════════════════════════════════
```

---

## 3. API Design (Phase 10a — Post-MVP)

### 3.1. Framework: FastAPI

### 3.2. Endpoints

| Method | Path | Description |
|:---|:---|:---|
| GET | `/health` | Health check |
| GET | `/api/v1/predict/{target_type}` | Get predictions for a date |
| GET | `/api/v1/backtest/{target_type}` | Get backtest summary |
| GET | `/api/v1/history/{date}` | Get draw results for a date |
| GET | `/api/v1/status` | DB status, data coverage |

### 3.3. Example Request/Response

```
GET /api/v1/predict/loto_2d_all_prizes?date=2024-01-16&model=logistic&top_k=20

Response:
{
  "predict_date": "2024-01-16",
  "target_type": "loto_2d_all_prizes",
  "model_name": "logistic_v1",
  "disclaimer": "Statistical analysis only. No accuracy guaranteed.",
  "predictions": [
    {"number": "68", "probability": 0.354, "rank": 1},
    ...
  ]
}
```

---

## 4. Dashboard Design (Phase 10b — Post-MVP)

### 4.1. Framework: Streamlit

### 4.2. Pages

1. **Predictions** — Chọn target type + date → hiển thị ranking.
2. **Backtest Results** — Chọn model + date range → hiển thị metrics chart.
3. **Data Explorer** — Xem draw results, frequency charts, gap charts.
4. **Model Comparison** — So sánh baselines vs ML models.

### 4.3. Disclaimer

Mọi trang dashboard phải hiển thị disclaimer:
> "Hệ thống này chỉ phục vụ nghiên cứu thống kê. Không đảm bảo kết quả dự đoán."
