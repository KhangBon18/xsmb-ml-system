# 15 — Agent Coding Prompts

Các prompt dưới đây thiết kế cho từng phase. Agent nhận prompt → đọc plan liên quan → code đúng scope → chạy test → báo cáo.

---

## Prompt: Phase 1 — Foundation

```
Bạn đang triển khai Phase 1 của xsmb-ml-system.

TRƯỚC KHI CODE, đọc kỹ các file plan sau:
- plans/2026-05-14-xsmb-plan-first/04_DATABASE_SCHEMA_PLAN.md
- plans/2026-05-14-xsmb-plan-first/01_DOMAIN_XSMB_DEFINITIONS.md
- plans/2026-05-14-xsmb-plan-first/14_DEFINITION_OF_DONE.md
- AGENTS.md

SCOPE Phase 1:
1. Implement xsmb/config.py:
   - PRIZE_STRUCTURE dict
   - PROJECT_ROOT, DATA_DIR, DB_PATH constants (dùng pathlib)
   - Logging setup function
   - LOTO_2D_NUMBERS, DB_3D_NUMBERS lists

2. Thêm xsmb/__init__.py (package init)

3. Implement xsmb/database/connection.py:
   - get_connection(db_path) → sqlite3.Connection (WAL mode, FK on)
   - init_db(db_path) → chạy schema.sql

4. Viết xsmb/database/schema.sql:
   - Full DDL cho 10 tables (copy từ 04_DATABASE_SCHEMA_PLAN.md)
   - PRAGMA statements

5. Implement xsmb/database/repository.py:
   - XSMBRepository class với basic CRUD methods
   - upsert_raw_result, insert_draw_results, insert_loto_2digits
   - insert_targets_* methods
   - get_* query methods

6. Sửa pyproject.toml:
   - Bỏ psycopg2-binary, sqlalchemy
   - Giữ lại: requests, beautifulsoup4, pandas, numpy, scikit-learn, fastapi, uvicorn, streamlit, python-dotenv, pydantic, pytest

7. Tạo tests/conftest.py:
   - test_db fixture (tmp_path)
   - sample_prizes fixture

KHÔNG ĐƯỢC code các module khác (scraping, processing, features, models).
KHÔNG MỞ RỘNG SCOPE.

Sau khi code xong, chạy:
- pytest tests/ -v
- python -c "from xsmb.database.connection import init_db; init_db()"

Báo cáo: files đã tạo/sửa, tests pass/fail, lỗi nếu có.
```

---

## Prompt: Phase 2 — Scraping

```
Bạn đang triển khai Phase 2 của xsmb-ml-system.

TRƯỚC KHI CODE, đọc kỹ:
- plans/2026-05-14-xsmb-plan-first/05_SCRAPING_AND_INGESTION_PLAN.md
- plans/2026-05-14-xsmb-plan-first/14_DEFINITION_OF_DONE.md
- AGENTS.md

SCOPE Phase 2:
1. Implement xsmb/scraping/sources.py:
   - Source dataclass
   - SOURCES dict với xoso_com_vn
   - DEFAULT_SOURCE

2. Implement xsmb/scraping/crawler.py:
   - crawl_date() — HTTP GET, save raw_content, idempotent
   - crawl_date_range() — sequential with sleep
   - Safety: timeout=10s, retry=3, backoff, User-Agent, sleep 1-3s
   - CrawlResult dataclass

3. Update xsmb/scraping/__init__.py

KHÔNG code parser, processing, features, models.
KHÔNG MỞ RỘNG SCOPE.

Test bằng cách crawl 1 ngày thực tế (chọn 1 ngày gần đây).
Xác minh raw HTML saved trong DB.

Báo cáo: files đã tạo/sửa, crawl test kết quả, lỗi nếu có.
```

---

## Prompt: Phase 3 — Parser + Validation

```
Bạn đang triển khai Phase 3 của xsmb-ml-system.

TRƯỚC KHI CODE, đọc kỹ:
- plans/2026-05-14-xsmb-plan-first/05_SCRAPING_AND_INGESTION_PLAN.md (phần parser)
- plans/2026-05-14-xsmb-plan-first/06_PROCESSING_AND_VALIDATION_PLAN.md
- plans/2026-05-14-xsmb-plan-first/01_DOMAIN_XSMB_DEFINITIONS.md
- plans/2026-05-14-xsmb-plan-first/14_DEFINITION_OF_DONE.md

SCOPE Phase 3:
1. Crawl 1 trang mẫu → inspect HTML structure → xác định selectors.
2. Implement xsmb/scraping/parser.py:
   - PrizeEntry dataclass
   - parse_xsmb_html(html, source_name)
   - Adapter cho xoso_com_vn

3. Implement xsmb/processing/normalize.py:
   - normalize_prize_tier()
   - normalize_winning_number()
   - TIER_ALIASES dict

4. Implement xsmb/processing/validate.py:
   - validate_draw()
   - ValidationResult dataclass

5. Implement xsmb/processing/transform.py:
   - extract_loto_2d()
   - extract_db_2cang()
   - extract_db_3cang()

6. Write tests:
   - tests/test_parser.py (P1-P7)
   - tests/test_normalize.py (N1-N5)
   - tests/test_transform.py [NEW] (T1-T4, LZ1-LZ4)
   - tests/test_validate.py [NEW] (V1-V5)

CRITICAL: Không bịa CSS selectors. Phải inspect real HTML trước.
CRITICAL: Leading zeros — dùng string slicing, không dùng int().

Chạy: pytest tests/test_parser.py tests/test_normalize.py tests/test_transform.py tests/test_validate.py -v
Báo cáo: files, test results, HTML structure findings.
```

---

## Prompt: Phase 4 — Target Builders

```
Bạn đang triển khai Phase 4 của xsmb-ml-system.

TRƯỚC KHI CODE, đọc kỹ:
- plans/2026-05-14-xsmb-plan-first/06_PROCESSING_AND_VALIDATION_PLAN.md (phần transform)
- plans/2026-05-14-xsmb-plan-first/07_TARGET_AND_FEATURE_PLAN.md (phần target builder)
- plans/2026-05-14-xsmb-plan-first/01_DOMAIN_XSMB_DEFINITIONS.md

SCOPE Phase 4:
1. Thêm vào xsmb/processing/transform.py:
   - build_targets_loto_2d(draw_date, loto_entries) → 100 rows
   - build_targets_db_2d(draw_date, special_number) → 100 rows
   - build_targets_db_3d(draw_date, special_number) → 1000 rows

2. Thêm target-related methods vào xsmb/database/repository.py.

3. Thêm tests vào tests/test_transform.py (T5-T10).

VALIDATION:
- loto_2d: 100 rows/date, sum(label) ≈ 23-25.
- db_2d: 100 rows/date, sum(label) = 1.
- db_3d: 1000 rows/date, sum(label) = 1.
- KHÔNG GỘP targets.

Chạy: pytest tests/test_transform.py -v
```

---

## Prompt: Phase 5 — Features

```
Bạn đang triển khai Phase 5 của xsmb-ml-system.

TRƯỚC KHI CODE, đọc kỹ:
- plans/2026-05-14-xsmb-plan-first/07_TARGET_AND_FEATURE_PLAN.md

SCOPE Phase 5:
1. xsmb/features/frequency_features.py — freq_7..freq_365
2. xsmb/features/gap_features.py — current_gap, max_gap, avg_gap
3. xsmb/features/rolling_features.py — rolling_hits_30, rolling_hits_60, hit_streak
4. xsmb/features/build_dataset.py — build_feature_dataset() orchestrator

CRITICAL: Mỗi feature function phải nhận target_date và filter data < target_date.
CRITICAL: Gọi _validate_no_leakage() trong mỗi feature function.

Write tests: tests/test_features.py (F1-F7).

Chạy: pytest tests/test_features.py -v
Output: CSV files in data/processed/
```

---

## Prompt: Phase 6 — Baselines

```
Bạn đang triển khai Phase 6 của xsmb-ml-system.

TRƯỚC KHI CODE, đọc kỹ:
- plans/2026-05-14-xsmb-plan-first/08_MODELING_PLAN.md (phần baselines)

SCOPE Phase 6:
1. xsmb/models/baseline.py:
   - random_baseline(numbers, target_type)
   - frequency_baseline(numbers, target_date, history, window=30)
   - gap_baseline(numbers, target_date, history)

2. tests/test_baseline.py [NEW] (B1-B5)

Baselines phải deterministic, output valid probabilities.
Chạy: pytest tests/test_baseline.py -v
```

---

## Prompt: Phase 7 — ML Training

```
Bạn đang triển khai Phase 7 của xsmb-ml-system.

TRƯỚC KHI CODE, đọc kỹ:
- plans/2026-05-14-xsmb-plan-first/08_MODELING_PLAN.md

SCOPE Phase 7:
1. xsmb/models/train.py — train_model(), calibrate_model()
2. xsmb/models/predict.py — predict()
3. xsmb/models/evaluate.py — brier_score(), precision_at_k(), hit_rate_at_k(), avg_hits_at_k()
4. tests/test_metrics.py [NEW] (M1-M4)

Model files saved to data/models/.
Chạy: pytest tests/test_metrics.py -v
```

---

## Prompt: Phase 8 — Backtest

```
Bạn đang triển khai Phase 8 của xsmb-ml-system.

TRƯỚC KHI CODE, đọc kỹ:
- plans/2026-05-14-xsmb-plan-first/09_BACKTEST_AND_METRICS_PLAN.md

SCOPE Phase 8:
1. xsmb/models/backtest.py — run_backtest(), report generation
2. tests/test_backtest.py (BT1-BT5)

CRITICAL: No random split. Expanding window.
CRITICAL: Train dates < test dates ALWAYS.
CRITICAL: Include baseline comparison.

Reports saved to data/reports/.
Chạy: pytest tests/test_backtest.py -v
```

---

## Prompt: Phase 9 — CLI

```
Bạn đang triển khai Phase 9 của xsmb-ml-system.

TRƯỚC KHI CODE, đọc kỹ:
- plans/2026-05-14-xsmb-plan-first/10_CLI_API_DASHBOARD_PLAN.md

SCOPE Phase 9:
1. app/main.py — argparse CLI
   - scrape, reparse, process, build-targets, build-features, train, backtest, predict, init-db
2. tests/test_cli.py [NEW] (C1-C3)

Wire together all modules from Phase 1-8.
Chạy: pytest tests/test_cli.py -v

Test end-to-end:
python -m app.main init-db
python -m app.main scrape --start-date 2024-01-01 --end-date 2024-01-07
python -m app.main process --start-date 2024-01-01 --end-date 2024-01-07
python -m app.main build-features --target loto_2d_all_prizes --start-date 2024-01-01 --end-date 2024-01-07
python -m app.main predict --target loto_2d_all_prizes --date 2024-01-08 --top-k 10
```
