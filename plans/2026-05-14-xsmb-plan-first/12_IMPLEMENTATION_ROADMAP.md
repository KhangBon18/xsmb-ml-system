# 12 — Implementation Roadmap

---

## Phase 1 — Foundation

**Mục tiêu:** Config, logging, database connection, schema, project setup.

### Deliverables
- [ ] `xsmb/config.py` — paths, constants, PRIZE_STRUCTURE, logging setup
- [ ] `xsmb/__init__.py` — package init
- [ ] `xsmb/database/connection.py` — `get_connection()`, `init_db()`
- [ ] `xsmb/database/schema.sql` — full DDL (10 tables)
- [ ] `xsmb/database/repository.py` — `XSMBRepository` class (basic CRUD)
- [ ] `xsmb/database/__init__.py` — exports
- [ ] `pyproject.toml` — sửa dependencies (bỏ psycopg2, thêm httpx nếu cần)
- [ ] `tests/conftest.py` — fixtures (test DB, sample data)

### Files touched
`xsmb/config.py`, `xsmb/__init__.py`, `xsmb/database/connection.py`, `xsmb/database/schema.sql`, `xsmb/database/repository.py`, `xsmb/database/__init__.py`, `pyproject.toml`, `tests/conftest.py`

### Tests
- `init_db()` tạo đúng 10 tables.
- `get_connection()` trả về connection với WAL + FK.
- `XSMBRepository` CRUD operations work.

### Done criteria
- [ ] `python -c "from xsmb.database.connection import init_db; init_db()"` tạo `data/xsmb.db` thành công.
- [ ] DB có 10 tables.
- [ ] `pytest tests/conftest.py` pass.

---

## Phase 2 — Data Ingestion (Scraping)

**Mục tiêu:** Crawl raw HTML từ web, lưu vào DB.

### Deliverables
- [ ] `xsmb/scraping/sources.py` — Source dataclass, SOURCES dict
- [ ] `xsmb/scraping/crawler.py` — `crawl_date()`, `crawl_date_range()`
- [ ] `xsmb/scraping/__init__.py` — exports

### Files touched
`xsmb/scraping/sources.py`, `xsmb/scraping/crawler.py`, `xsmb/scraping/__init__.py`

### Tests
- Crawl 1 ngày → raw HTML saved.
- Idempotent: crawl lại → skip.
- Force: crawl lại → overwrite.
- Timeout handling.

### Done criteria
- [ ] Crawl 1 ngày thành công, raw_content trong DB.
- [ ] Crawl 7 ngày → 7 raw_results rows (hoặc ít hơn nếu có ngày nghỉ).
- [ ] Rate limiting hoạt động (sleep giữa requests).

---

## Phase 3 — Parser + Validation

**Mục tiêu:** Parse raw HTML → structured data, validate, extract loto 2D.

### Deliverables
- [ ] `xsmb/scraping/parser.py` — `parse_xsmb_html()`, adapter per source
- [ ] `xsmb/processing/normalize.py` — `normalize_prize_tier()`, `normalize_winning_number()`
- [ ] `xsmb/processing/validate.py` — `validate_draw()`, `ValidationResult`
- [ ] `xsmb/processing/transform.py` — `extract_loto_2d()`, `extract_db_2cang()`, `extract_db_3cang()`
- [ ] `tests/test_parser.py` — P1-P7
- [ ] `tests/test_normalize.py` — N1-N5
- [ ] `tests/test_transform.py` — T1-T4, LZ1-LZ4 [NEW FILE]
- [ ] `tests/test_validate.py` — V1-V5 [NEW FILE]

### Files touched
`xsmb/scraping/parser.py`, `xsmb/processing/normalize.py`, `xsmb/processing/validate.py`, `xsmb/processing/transform.py`, `tests/test_parser.py`, `tests/test_normalize.py`, `tests/test_transform.py`, `tests/test_validate.py`

### Tests
- Parse valid HTML → 27 entries.
- Leading zeros preserved.
- Invalid HTML → error.
- Extraction: "45678" → "78" (2D), "678" (3D).
- Validation: 27 pass, 26 fail, 28 fail.

### Done criteria
- [ ] Parse 1 real HTML page → 27 valid PrizeEntry.
- [ ] `pytest tests/test_parser.py tests/test_normalize.py tests/test_transform.py tests/test_validate.py` — ALL PASS.

---

## Phase 4 — Target Builders

**Mục tiêu:** Build target datasets cho 3 target types.

### Deliverables
- [ ] `xsmb/processing/transform.py` — thêm `build_targets_loto_2d()`, `build_targets_db_2d()`, `build_targets_db_3d()`
- [ ] `xsmb/database/repository.py` — thêm target insert/query methods
- [ ] `tests/test_transform.py` — T5-T10

### Files touched
`xsmb/processing/transform.py`, `xsmb/database/repository.py`, `tests/test_transform.py`

### Tests
- loto_2d: 100 rows/date, labels correct, actual_hits correct.
- db_2d: 100 rows/date, exactly 1 positive.
- db_3d: 1000 rows/date, exactly 1 positive.
- Targets not mixed.

### Done criteria
- [ ] Build targets cho 1 ngày → correct row counts.
- [ ] `sum(label)` cho db_2d = 1, cho db_3d = 1.
- [ ] All leading zeros preserved.

---

## Phase 5 — Features

**Mục tiêu:** Sinh feature dataset cho mỗi target type.

### Deliverables
- [ ] `xsmb/features/frequency_features.py` — freq_7, freq_14, ..., freq_365
- [ ] `xsmb/features/gap_features.py` — current_gap, max_gap, avg_gap
- [ ] `xsmb/features/rolling_features.py` — rolling_hits, hit_streak
- [ ] `xsmb/features/build_dataset.py` — `build_feature_dataset()` orchestrator
- [ ] `tests/test_features.py` — F1-F7

### Files touched
`xsmb/features/*.py`, `tests/test_features.py`

### Tests
- No future leakage.
- Frequency counts correct.
- Gap calculations correct.
- Output column consistency.

### Done criteria
- [ ] Build features cho loto_2d, 1 tháng → CSV output.
- [ ] No leakage test passes.
- [ ] `pytest tests/test_features.py` — ALL PASS.

---

## Phase 6 — Baselines

**Mục tiêu:** Implement 3 baseline models.

### Deliverables
- [ ] `xsmb/models/baseline.py` — `random_baseline()`, `frequency_baseline()`, `gap_baseline()`
- [ ] `tests/test_baseline.py` — B1-B5 [NEW FILE]

### Files touched
`xsmb/models/baseline.py`, `tests/test_baseline.py`

### Tests
- Random: uniform probabilities.
- Frequency: ranking matches freq order.
- Deterministic.
- Valid probabilities.

### Done criteria
- [ ] All 3 baselines produce valid output for all 3 target types.
- [ ] `pytest tests/test_baseline.py` — ALL PASS.

---

## Phase 7 — ML Training

**Mục tiêu:** Train Logistic Regression + HistGradientBoosting, calibrate, save/load.

### Deliverables
- [ ] `xsmb/models/train.py` — `train_model()`, calibration wrapper
- [ ] `xsmb/models/predict.py` — `predict()`
- [ ] `xsmb/models/evaluate.py` — metric functions (Brier, P@K, Hit@K, Avg@K)
- [ ] `tests/test_metrics.py` — M1-M4 [NEW FILE]

### Files touched
`xsmb/models/train.py`, `xsmb/models/predict.py`, `xsmb/models/evaluate.py`, `tests/test_metrics.py`

### Tests
- Train on sample data → model object.
- Predict → valid probabilities.
- Metrics compute correctly.
- Model save/load roundtrip.

### Done criteria
- [ ] Train logistic on loto_2d → model file in `data/models/`.
- [ ] Predict → 100 ranked numbers.
- [ ] Metric functions verified.

---

## Phase 8 — Backtest

**Mục tiêu:** Walk-forward backtest framework + reports.

### Deliverables
- [ ] `xsmb/models/backtest.py` — `run_backtest()`, report generation
- [ ] `tests/test_backtest.py` — BT1-BT5

### Files touched
`xsmb/models/backtest.py`, `tests/test_backtest.py`

### Tests
- No random split.
- Expanding window.
- Metrics computed.
- CSV format correct.
- Baseline comparison included.

### Done criteria
- [ ] Backtest loto_2d logistic 1 month → CSV report.
- [ ] Baseline comparison table in report.
- [ ] `pytest tests/test_backtest.py` — ALL PASS.

---

## Phase 9 — CLI

**Mục tiêu:** Wire everything together via CLI.

### Deliverables
- [ ] `app/main.py` — argparse CLI with all commands
- [ ] `tests/test_cli.py` — C1-C3 [NEW FILE]

### Files touched
`app/main.py`, `tests/test_cli.py`

### Tests
- Help command works.
- init-db works.
- Each command accepts correct args.

### Done criteria
- [ ] Full pipeline via CLI: scrape → process → build-features → train → backtest → predict.
- [ ] `pytest tests/test_cli.py` — ALL PASS.

---

## Phase 10 — API + Dashboard (Post-MVP)

**Mục tiêu:** FastAPI endpoints + Streamlit dashboard.

### Deliverables
- [ ] `xsmb/api/routes.py` — FastAPI endpoints
- [ ] `xsmb/api/schemas.py` — Pydantic models
- [ ] `xsmb/dashboard/streamlit_app.py` — Dashboard pages
- [ ] `app/main.py` — thêm `serve` command

### Files touched
`xsmb/api/routes.py`, `xsmb/api/schemas.py`, `xsmb/dashboard/streamlit_app.py`, `app/main.py`

### Done criteria
- [ ] API serves predictions.
- [ ] Dashboard displays data.
- [ ] Only after Phase 1-9 complete.

---

## Summary Timeline

| Phase | Priority | Est. Effort | Dependencies |
|:---|:---|:---|:---|
| Phase 1 Foundation | 🔴 Critical | 2-3 hours | None |
| Phase 2 Scraping | 🔴 Critical | 3-4 hours | Phase 1 |
| Phase 3 Parser | 🔴 Critical | 3-4 hours | Phase 2 |
| Phase 4 Targets | 🔴 Critical | 2-3 hours | Phase 3 |
| Phase 5 Features | 🔴 Critical | 4-6 hours | Phase 4 |
| Phase 6 Baselines | 🔴 Critical | 2-3 hours | Phase 4 |
| Phase 7 ML | 🟡 Important | 3-4 hours | Phase 5 |
| Phase 8 Backtest | 🟡 Important | 4-6 hours | Phase 6, 7 |
| Phase 9 CLI | 🟡 Important | 3-4 hours | Phase 1-8 |
| Phase 10 API/Dashboard | 🟢 Nice-to-have | 4-6 hours | Phase 9 |
