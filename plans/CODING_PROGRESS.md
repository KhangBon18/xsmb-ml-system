# Coding Progress

## Phase 1 - Domain Core, Normalize, Validate, Transform

Status: Complete
Date: 2026-05-14

Scope override applied: database, scraper, features, ML, backtest, API, dashboard,
and Docker work are intentionally not implemented in Phase 1.

Implemented:
- XSMB domain constants and target type constants.
- Strict string-preserving `normalize_number`.
- Tail digit extraction with leading zero preservation.
- Candidate spaces for `loto_2d_all_prizes`, `db_2cang`, and `db_3cang`.
- Complete draw validation for exactly 27 XSMB prize rows.
- Target extraction for all-prize loto 2D, special-prize 2-cang, and special-prize 3-cang.
- Daily target hit and label builders.

Tests:
- Added normalization tests for leading zeros, string-only input, digit checks, and length checks.
- Added validation tests for complete draws, wrong counts, wrong tier counts, wrong lengths, and non-digits.
- Added transform tests for candidate spaces, tail extraction, all target types, hit counts, and special-only target extraction.

Commands run:
- `python -m pytest tests/test_normalize.py tests/test_parser.py tests/test_features.py tests/test_backtest.py -q`
  - Result: failed to start because `python` is not available on PATH.
- `python -m pytest tests/ -q`
  - Result: failed to start because `python` is not available on PATH.
- `python3 -m pytest tests/test_normalize.py tests/test_parser.py tests/test_features.py tests/test_backtest.py -q`
  - Result: 5 passed.
- `python3 -m pytest tests/ -q`
  - Result: 20 passed.
- `python3 -c "from xsmb.config import PRIZE_SPECS; from xsmb.processing.transform import candidate_space; assert len(candidate_space('db_3cang')) == 1000; print('phase1 import ok')"`
  - Result: passed.

Blockers and assumptions:
- The local shell has `python3` but not `python`; verification used `python3`.
- Existing parser, feature, and backtest test files are still empty by design because those implementations are outside Phase 1.
- No database, scraper, feature, ML, backtest, API, dashboard, or Docker code was implemented.

Recommended next phase:
- Phase 2 should begin database foundation only if explicitly approved under the user's phase gate.

## Phase 2A - Database Config and Session Foundation

Status: Complete
Date: 2026-05-14

Scope guard:
- Implemented only database configuration/session foundation.
- No full repository layer, scraper, features, ML/backtest, API/dashboard, Docker,
  or database schema work was implemented.

Implemented:
- Added default MVP `DATABASE_URL`: `sqlite:///data/xsmb.sqlite3`.
- Added `get_database_url()` to resolve environment override or fallback.
- Added SQLAlchemy `create_engine_from_url()` engine factory.
- Added SQLite parent directory auto-create for file-based SQLite URLs.
- Added clean handling for in-memory SQLite URLs.
- Added `create_session_factory()` and `get_session()` helpers.
- Exported database connection helpers from `xsmb.database`.
- Updated `.env.example` to use `DATABASE_URL`.
- Removed the PostgreSQL-only `psycopg2-binary` dependency from `pyproject.toml`.

Tests:
- Added database connection tests for default URL resolution.
- Added environment override test.
- Added temporary file-based SQLite connection test.
- Added in-memory SQLite connection test.
- Added parent directory auto-create test.
- Added session factory and `get_session()` test.
- Added guard that tests do not touch `data/xsmb.sqlite3`.

Commands run:
- `python3 -m pytest tests/test_database_connection.py -q`
  - Result: 7 passed.
- `python3 -m pytest tests/ -q`
  - Result: 27 passed.

Blockers and assumptions:
- Verification used `python3`, matching the Phase 2A instruction.
- SQLAlchemy is the only required database library for this phase.
- PostgreSQL remains optional for a later phase and is not configured here.

Recommended next phase:
- Phase 2B should define SQLAlchemy metadata/models and/or schema only after
  explicit approval.

## Phase 2B - ORM Models and Schema

Status: Complete
Date: 2026-05-14

Scope guard:
- Implemented only SQLAlchemy ORM models, schema documentation, and model tests.
- No repository layer, scraper, features, ML/backtest, API/dashboard, Docker, or
  Phase 2C work was implemented.

Implemented:
- Added SQLAlchemy ORM models for `raw_pages`, `draws`, `prizes`, `targets`,
  `feature_snapshots`, `model_runs`, and `predictions`.
- Added `Base`, `init_db(engine)`, and `drop_db(engine)` helpers.
- Added draw-date uniqueness for XSMB draws.
- Added prize uniqueness on `draw_id + prize_tier + prize_index`.
- Added target uniqueness on `draw_id + target_type + candidate_number`.
- Added foreign-key relationships for prizes/targets to draws and predictions
  to model runs.
- Preserved lottery numbers as string/Text columns.
- Enabled SQLite foreign-key enforcement in the engine factory.
- Updated `schema.sql` as SQL schema documentation matching the ORM tables.
- Exported ORM models and helpers from `xsmb.database`.

Tests:
- Added table creation test in temporary SQLite.
- Added unique draw date constraint test.
- Added leading-zero preservation tests for prize and target numbers.
- Added foreign-key enforcement test.
- Added unique prize and target constraint tests.
- Added JSON/text storage and reload test.
- Added nullable/enforced prediction model-run foreign key test.

Commands run:
- `python3 -m pytest tests/test_database_models.py -q`
  - Initial result: 1 failed, 8 passed because SQLite raised FK violations on
    `execute()` rather than `commit()`.
- `python3 -m pytest tests/ -q`
  - Initial result: 1 failed, 35 passed for the same FK assertion issue.
- `python3 -m pytest tests/test_database_models.py -q`
  - Final result: 9 passed.
- `python3 -m pytest tests/ -q`
  - Final result: 36 passed.

Blockers and assumptions:
- No blockers.
- Verification used temporary SQLite databases only.
- `schema.sql` is documentation/DDL; ORM metadata is the implementation source
  of truth for table creation in this phase.

Recommended next phase:
- Phase 2C should implement the repository/data-access layer only after
  explicit approval.

## Phase 2C - Repositories and Database Tests

Status: Complete
Date: 2026-05-14

Scope guard:
- Implemented only database repository classes and repository tests.
- No scraper, features, ML/backtest, API/dashboard, Docker, or Phase 3 work was
  implemented.

Implemented:
- Added `RawPageRepository` with insert and checksum lookup/idempotency.
- Added `DrawRepository` with create/get-by-date idempotency and status update.
- Added `PrizeRepository` for saving and reading complete 27-prize draw rows.
- Added deterministic duplicate prize handling: exact duplicate saves are
  idempotent, conflicting duplicate prize values raise `ValueError`.
- Added `TargetRepository` that generates targets from stored prizes using
  Phase 1 transform functions.
- Added idempotent target generation for `loto_2d_all_prizes`, `db_2cang`, and
  `db_3cang`.
- Added `FeatureSnapshotRepository` with basic insert/list.
- Added `ModelRunRepository` with basic create/get/list.
- Added `PredictionRepository` with basic save and top-k list.
- Exported repository classes from `xsmb.database`.

Tests:
- Added temporary-SQLite repository fixture.
- Added raw page checksum idempotency test.
- Added draw create/get/update test.
- Added 27-prize save/read exactness test.
- Added leading-zero DB save/load coverage through prize and target rows.
- Added duplicate prize idempotency and conflict tests.
- Added target generation tests for all three target types.
- Added target regeneration idempotency test.
- Added special-prize-only target extraction test.
- Added basic feature snapshot, model run, and prediction repository tests.

Commands run:
- `python3 -m pytest tests/test_database_repository.py -q`
  - Result: 12 passed.
- `python3 -m pytest tests/ -q`
  - Result: 48 passed.

Blockers and assumptions:
- No blockers.
- Repository methods flush but do not commit; transaction boundaries remain with
  the caller/session.
- Tests used temporary SQLite databases only.

Recommended next phase:
- Phase 3 should begin scraper/parser work only after explicit approval.

## Phase 3 - Scraping Source Config, Parser, and Ingestion

Status: Complete
Date: 2026-05-14

Scope guard:
- Implemented only XSMB source configuration, safe HTTP fetching, static HTML
  parsing, and small ingestion integration.
- No features, ML, backtest, API, dashboard, Docker, scheduler, broad crawling,
  or Phase 4 work was implemented.

Implemented:
- Fast-forwarded `feat/phase-3-scraper-parser` onto merged Phase 2 code from
  `origin/main` before starting Phase 3.
- Added `XSMBSourceConfig`, `get_default_xsmb_source()`, and
  `build_result_url()`.
- Added safe `fetch_url()` with timeout, clear User-Agent, two-attempt retry
  behavior, small backoff, and `FetchError`.
- Added `parse_xsmb_result_html()` for static XSMB HTML strings.
- Parser emits Phase 1-compatible rows:
  `draw_date`, `prize_tier`, zero-based `prize_index`, `winning_number`.
- Parser preserves leading zeros and validates final output with
  `validate_draw_results()`.
- Parser fails clearly for missing tier sections, wrong counts, wrong lengths,
  duplicate/malformed sections, and empty HTML.
- Added `ingest_xsmb_html()` to save raw HTML, create/get draw, save 27 prizes,
  and optionally generate all three target types using Phase 2 repositories.
- Ingestion is idempotent for same raw checksum, draw date, prize rows, and
  generated target rows.
- Added static fixture `tests/fixtures/xsmb_sample_result.html` with nested tags
  and leading-zero examples.

Tests:
- Added parser fixture tests for 27 rows, leading zeros, tier mapping,
  validation compatibility, missing special prize, wrong prize count, wrong
  number length, and duplicate sections.
- Added crawler tests using mocked `requests.get`; no live network is used.
- Added ingestion tests using temporary SQLite only.
- Added ingestion tests for raw page, draw, prize persistence, all target types,
  special-prize-only target extraction, and idempotency.

Commands run:
- `git merge --ff-only origin/main`
  - Result: Phase 3 branch fast-forwarded to merged Phase 2 base.
- `python3 -m pytest tests/test_parser.py -q`
  - Result: 8 passed.
- `python3 -m pytest tests/test_crawler.py -q`
  - Result: 4 passed.
- `python3 -m pytest tests/test_ingestion.py -q`
  - Result: 3 passed.
- `python3 -m pytest tests/ -q`
  - Result: 63 passed.

Blockers and assumptions:
- No blockers.
- Parser fixture uses explicit `data-prize-tier` and `data-winning-number`
  attributes, with fallback parsing for whitespace/nested markup.
- Crawler tests use mocks only and do not contact live websites.
- Ingestion leaves transaction commit control to the caller/session.
- Tests used temporary SQLite databases only.

Recommended next phase:
- Phase 4 should build target-processing orchestration or next approved scope
  only after explicit approval.

## Phase 4 - Leakage-Safe Feature Engineering

Status: Complete
Date: 2026-05-14

Scope guard:
- Implemented only pure feature engineering for target history rows.
- No baselines, ML train/predict, backtest, API, dashboard, Docker, CLI, or
  Phase 5 work was implemented.

Implemented:
- Added frequency feature helpers for `freq_7`, `freq_14`, `freq_30`,
  `freq_60`, `freq_90`, and `freq_180`.
- Added `hit_count_sum_30`.
- Added draw-index gap helpers for `current_gap`, `days_since_last_seen`,
  `max_gap_before_target`, and `avg_gap_before_target`.
- Added rolling hit-rate helpers for `rolling_hit_rate_30` and
  `rolling_hit_rate_90`.
- Added public `build_feature_dataset(history_df, target_type, start_date=None,
  end_date=None, min_history_days=30)`.
- Builder validates required columns, validates supported target types using
  Phase 1 candidate-space logic, filters by explicit target type, preserves
  candidate strings/leading zeros, does not mutate caller input, and returns
  deterministic ordering by target date then candidate number.
- All features use only rows where `draw_date < target_date`.
- `min_history_days` uses count of prior available draw dates, not calendar
  days.

Tests:
- Added expected-column coverage.
- Added coverage for all target types: `loto_2d_all_prizes`, `db_2cang`, and
  `db_3cang`.
- Added leading-zero preservation checks for `00`, `05`, and `008`.
- Added explicit no-leakage test where a target-date-only hit must not affect
  frequency or rolling-rate features.
- Added hit-count, gap, rolling-rate, min-history, date-filter, input-mutation,
  deterministic-order, unsupported-target, and missing-column tests.

Commands run:
- `python3 -m pytest tests/test_features.py -q`
  - Result: 16 passed.
- `python3 -m pytest tests/ -q`
  - Result: 79 passed.

Blockers and assumptions:
- No blockers.
- Feature rows are generated only for candidate/date rows present in the input
  history DataFrame. Full 100/1000-row outputs are supported when the input
  history contains full target rows from Phase 3 ingestion.
- Feature generation is pure pandas and does not write to the database.

Recommended next phase:
- Phase 5 should implement baseline ranking models only after explicit
  approval.

## Phase 5 - Baselines, Metrics, and Walk-Forward Backtest

Status: Complete
Date: 2026-05-14

Scope guard:
- Implemented only deterministic baselines, evaluation metrics, and pure
  walk-forward backtest orchestration.
- No ML train/predict pipelines, logistic regression, tree models, CLI, API,
  dashboard, Docker, scheduler, or Phase 6 work was implemented.

Implemented:
- Added supported baselines: `random_uniform`, `frequency_30`,
  `frequency_90`, and `gap_rank`.
- Added `score_baseline_candidates(feature_df, model_name)` with deterministic
  per-date ranking, lexicographic tie-breaking, probability clipping, and
  string-preserving candidate output.
- Added evaluation metrics: `brier_score`, `log_loss`, `precision_at_k`,
  `hit_rate_at_k`, `avg_hits_at_k`, `recall_at_k`, `calibration_by_bucket`,
  and `evaluate_predictions`.
- Added `run_walk_forward_backtest()` that builds Phase 4 leakage-safe features,
  scores baseline predictions, evaluates summary metrics, and returns
  predictions/calibration DataFrames.
- Added small report helpers `summarize_backtest_result()` and
  `predictions_to_records()`.
- Exported Phase 5 helpers from `xsmb.models`.

Tests:
- Added baseline tests for uniform probabilities, frequency ranking, gap
  ranking, leading-zero preservation, unsupported models, and missing columns.
- Added metric tests for Brier score, clipped log loss, Precision@K,
  HitRate@K, AvgHits@K, Recall@K, calibration buckets, and summary keys.
- Added walk-forward tests for all target types, min-history behavior,
  date-window filtering, required prediction columns, rank starts at 1, and
  an explicit no-leakage target-date hit case.

Commands run:
- `python3 -m pytest tests/test_backtest.py -q`
  - Initial result: 1 failed, 19 passed due to a test assertion using
    `pytest.approx` inside a set.
- `python3 -m pytest tests/test_backtest.py -q`
  - Final result: 20 passed.
- `python3 -m pytest tests/ -q`
  - Result: 99 passed.

Blockers and assumptions:
- No blockers.
- Backtest is time-based through Phase 4 feature generation and does not use
  random splits.
- Recall skips dates with no positive labels.
- Baselines do not use current target labels to create scores/probabilities;
  labels are used only by evaluation after prediction rows are produced.

Recommended next phase:
- Phase 6 should implement ML training/prediction models only after explicit
  approval.

## Phase 6 - ML Training and Prediction

Status: Complete
Date: 2026-05-14

Scope guard:
- Implemented only ML training, prediction, and artifact utilities.
- No CLI, FastAPI, Streamlit dashboard, Docker, scheduler, broad crawling, or
  Phase 7 work was implemented.

Implemented:
- Added supported ML models: `logistic_regression`, `random_forest`, and
  `hist_gradient_boosting` when available in sklearn.
- Added `train_model()` with target-type validation, model-name validation,
  numeric feature selection, explicit feature-column support, one-class checks,
  deterministic random state, and sklearn pipelines.
- Added logistic regression with imputation/scaling and balanced class weights.
- Added random forest and hist-gradient boosting training with deterministic
  defaults.
- Added safe calibration for tree models only when enough positive/negative
  samples exist; metadata records whether calibration was used.
- Added `predict_probabilities()` with exact feature-column usage, target-type
  filtering, optional target-date filtering, top-k filtering, probability
  clipping, per-date ranking, and lexicographic tie-breaking.
- Added artifact helpers `save_model_artifact()` and `load_model_artifact()`
  using pickle.
- Added `.gitignore` entries for Python bytecode and generated model artifacts.
- Exported Phase 6 helpers from `xsmb.models`.

Tests:
- Added deterministic synthetic ML tests for logistic regression, random forest,
  and hist-gradient boosting availability/graceful behavior.
- Added validation tests for unsupported models, empty data, one-class data,
  missing labels, and no numeric features.
- Added prediction tests for required columns, valid probabilities, rank starts
  at 1, lexicographic tie-breaks, top-k filtering, target-date filtering, and
  leading-zero preservation for `00`, `05`, and `008`.
- Added artifact roundtrip tests using a temporary directory only.
- Added integration tests for all target types and Phase 5 evaluation
  compatibility.
- Added guard that ML training/prediction does not create the real SQLite DB.

Commands run:
- `python3 -m pytest tests/test_ml_train_predict.py -q`
  - Result: 21 passed.
- `python3 -m pytest tests/ -q`
  - Result: 120 passed.
- `grep -RInE "guaranteed|sure win|high accuracy guarantee|chắc chắn ra|kèo chắc" README.md xsmb app tests plans 2>/dev/null || true`
  - Result: found only disclaimer/checklist references in planning docs.

Blockers and assumptions:
- No blockers.
- sklearn is available locally (`1.8.0`), including
  `HistGradientBoostingClassifier`.
- Tests use synthetic data only and do not require DB writes or network access.
- Generated model artifacts are not committed; artifact tests use temp dirs.

Recommended next phase:
- Phase 7 should implement CLI/API integration only after explicit approval.

## Phase 7A - CLI Skeleton with argparse

Status: Complete
Date: 2026-05-14

Scope guard:
- Implemented only CLI argument parsing and MVP stub handlers.
- No FastAPI, Streamlit dashboard, Docker, scheduler, broad crawling, network
  requests, or real database writes were implemented.

Implemented:
- Added `app/__init__.py` to make `app` a proper Python package.
- Added `app/main.py` with `main(argv=None) -> int` entry point.
- Added `build_parser()` with six subcommands: `scrape`, `process`,
  `build-features`, `backtest`, `train`, `predict`.
- All subcommands validate arguments via `argparse.choices` for target types
  and model names.
- Added `--start-date`/`--end-date` validation (YYYY-MM-DD format, real
  calendar dates).
- Added `--top-k` positive-integer validation.
- Target type choices use `xsmb.config.TARGET_TYPES`.
- Backtest model choices use `SUPPORTED_BASELINES`.
- Train model choices use `SUPPORTED_ML_MODELS`.
- All handlers print safe MVP stub messages and return exit code 0.
- No network requests are made.
- No database is created or modified.
- Module is runnable via `python -m app.main`.

Tests:
- Added `tests/test_cli.py` with 37 tests covering:
  - Top-level help exits 0.
  - No-command returns 1.
  - Per-subcommand help exits 0.
  - Invalid target_type rejection (argparse exit code 2).
  - All valid target types accepted for build-features.
  - top_k zero/negative/non-integer rejection.
  - top_k positive acceptance.
  - Invalid date format rejection.
  - Impossible calendar date rejection.
  - Valid date acceptance for scrape and process.
  - MVP stub messages in stdout for all six commands.
  - No real database creation guard.
  - Invalid model names rejected for backtest and train.
  - Leading-zero preservation of target type strings.
  - Module runnable via subprocess (`--help` and no-args).

Commands run:
- `python3 -m pytest tests/test_cli.py -q`
  - Result: 37 passed.
- `python3 -m pytest tests/ -q`
  - Result: 157 passed (120 existing + 37 new).

Blockers and assumptions:
- No blockers.
- All command handlers are MVP stubs only.
- FastAPI endpoints are deferred to Phase 7B.

Recommended next phase:
- Phase 7B should wire CLI commands to real Phase 4/5/6 functions via CSV.

## Phase 7B - CLI Wiring to Pure Functions via CSV I/O

Status: Complete
Date: 2026-05-14

Scope guard:
- Implemented only CSV-based wiring for backtest, train, and predict CLI
  commands to existing Phase 4/5/6 pure functions.
- No FastAPI, Streamlit dashboard, Docker, scheduler, broad crawling, or
  live network requests implemented.
- No real database created or modified.

Implemented:
- Added `--history-csv` to `backtest` subcommand; when present, reads CSV
  with pandas and calls `run_walk_forward_backtest()` + `summarize_backtest_result()`,
  printing summary JSON to stdout.
- Added `--features-csv` and `--artifact-dir` to `train` subcommand; when
  `--features-csv` is present, reads CSV with pandas, calls `train_model()` +
  `save_model_artifact()`, and prints JSON with artifact_path/model_name/
  target_type/row_count.
- Added `--features-csv` and `--artifact` to `predict` subcommand; when both
  are present, loads artifact with `load_model_artifact()`, reads CSV, calls
  `predict_probabilities()`, and prints JSON prediction records.
- Added `_read_csv_safe()` helper that forces `candidate_number`, `draw_date`,
  `target_date`, and `target_type` columns to string dtype on read, preserving
  leading zeros.
- Without new CSV arguments, all three commands retain safe MVP stub messages.
- Missing/invalid CSV or artifact paths raise clear `SystemExit` errors.

Tests:
- Updated `tests/test_cli.py` from 37 → 51 tests. Added 14 Phase 7B tests:
  - Backtest with synthetic history CSV prints summary JSON with brier_score.
  - Backtest without CSV stays MVP stub.
  - Backtest with missing CSV fails clearly.
  - Train with synthetic feature CSV saves artifact to temp dir.
  - Train without CSV stays MVP stub.
  - Train with missing CSV fails clearly.
  - Predict with temp artifact + feature CSV prints prediction JSON.
  - Predict without CSV stays MVP stub.
  - Predict without artifact stays MVP stub.
  - Predict with missing artifact fails clearly.
  - Predict with missing features CSV fails clearly.
  - CLI predict preserves "00" and "05" as 2-char strings (loto_2d_all_prizes).
  - CLI predict preserves "008" and "000" as 3-char strings (db_3cang).
  - Wired commands do not create the real SQLite database.
- Synthetic data uses deterministic DataFrames with 40+ dates for backtest
  and both positive/negative labels for train/predict.
- Feature columns include: freq_7, freq_14, freq_30, freq_60, freq_90,
  freq_180, hit_count_sum_30, current_gap, days_since_last_seen,
  max_gap_before_target, avg_gap_before_target, rolling_hit_rate_30,
  rolling_hit_rate_90.

Commands run:
- `python3 -m pytest tests/test_cli.py -q`
  - Result: 51 passed.
- `python3 -m pytest tests/ -q`
  - Result: 171 passed (120 existing + 51 CLI).

Blockers and assumptions:
- No blockers.
- CSV reading uses pandas `dtype={col: str}` to preserve leading zeros on
  candidate_number and date columns.
- All tests use temporary directories only; no real DB or network is touched.
- scrape, process, and build-features remain MVP stubs.

Recommended next phase:
- Phase 7C should implement FastAPI endpoints only after explicit approval.

## Phase 7C - FastAPI Minimal Foundation

Status: Complete
Date: 2026-05-14

Scope guard:
- Implemented minimal FastAPI foundation only (`/health` and `/targets`).
- `POST /predict` and `POST /backtest` are explicitly deferred.
- No Streamlit dashboard, Docker, scheduler, broad crawling, network,
  or real DB work was implemented.
- Ensured graceful fallback and test execution if FastAPI/Pydantic are missing.

Implemented:
- `xsmb/api/__init__.py`: Package init.
- `xsmb/api/schemas.py`: Pydantic schemas for `HealthResponse` and `TargetsResponse`
  (graceful handling of missing `pydantic`).
- `xsmb/api/routes.py`: FastAPI router with `GET /health` and `GET /targets` endpoints.
  Returns correct target types preserving project constants.
- `app/main.py`: Added `create_api_app()` ASGI factory, safely bypassing missing FastAPI
  so `python -m app.main` CLI execution and tests never break.

Tests:
- Created `tests/test_api.py`.
- Tests for `GET /health` HTTP 200, status "ok", and service name.
- Tests for `GET /targets` HTTP 200 and listing all three target types
  (`loto_2d_all_prizes`, `db_2cang`, `db_3cang`).
- Tests gracefully skip if FastAPI is not installed (`HAS_FASTAPI`).
- All previous CLI and domain test suites remain fully intact and green.

Commands run:
- `python3 -m pytest tests/test_api.py -q`
  - Result: 4 passed.
- `python3 -m pytest tests/test_cli.py -q`
  - Result: 51 passed.
- `python3 -m pytest tests/ -q`
  - Result: 175 passed (171 existing + 4 API).
- Checked for forbidden language (`grep` for "guaranteed", etc.)
  - Result: No forbidden predictions claimed in implementation code.

Blockers and assumptions:
- No blockers.
- `fastapi` and `pydantic` are assumed to be optional dependencies for CLI tools.
- ASGI entry point `app.main:api_app` is ready.

Recommended next phase:
- Phase 7D should implement `POST /predict` and `POST /backtest` endpoints only after explicit approval.
