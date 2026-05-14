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
