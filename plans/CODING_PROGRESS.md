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
