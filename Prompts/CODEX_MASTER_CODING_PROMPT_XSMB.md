# CODEX MASTER CODING PROMPT — XSMB ML SYSTEM

Use this prompt inside Codex from the repository root. The repo is for **Xổ Số Miền Bắc (XSMB)** only. Do not generalize to Miền Nam/Miền Trung unless explicitly requested later.

---

## 0. Operating Mode

You are a senior Python engineer + ML systems engineer. You are working on an existing repo named `xsmb-ml-system`.

Your job is to implement the project **phase by phase**, with tests, without breaking the existing structure.

Do **not** code everything in one giant diff. Work in small, reviewable phases. After each phase, stop and report:

1. What files changed.
2. What was implemented.
3. What tests were added/updated.
4. Exact commands run.
5. Test results.
6. Any blockers or assumptions.
7. What the next phase should be.

Do not proceed to the next phase until explicitly told:

```text
APPROVE PHASE N, CONTINUE PHASE N+1
```

---

## 1. First Actions Before Coding

Before changing code, do this:

1. Read these files completely:
   - `AGENTS.md`
   - `README.md`
   - `PROJECT_SPEC.md`
   - `DATA_CONTRACT.md`
   - `MODEL_SPEC.md`
   - `BACKTEST_SPEC.md`
   - the latest folder under `plans/` if it exists
2. Inspect the current package layout:
   - `xsmb/`
   - `app/`
   - `tests/`
   - `pyproject.toml`
3. Confirm that this repo is currently mostly scaffolding/empty implementation.
4. Create or update this file:

```text
plans/CODING_PROGRESS.md
```

Log each phase there as you complete it.

Do not remove any existing spec unless the implementation requires a careful additive update.

---

## 2. Non-Negotiable Domain Rules

This project is for XSMB only.

A valid XSMB draw has exactly 27 prize numbers:

```text
special: 1 number, length 5
first:   1 number, length 5
second:  2 numbers, length 5
third:   6 numbers, length 5
fourth:  4 numbers, length 4
fifth:   6 numbers, length 4
sixth:   3 numbers, length 3
seventh: 4 numbers, length 2
```

Total: 27 numbers.

All numbers must be strings. Preserve leading zeros forever.

Examples:

```text
"00" must not become 0
"05" must not become 5
"007" must not become 7
```

Never cast lottery numbers to int except for non-persistent internal sorting where the original string is preserved.

---

## 3. Target Types To Support

The original repo mainly describes `loto_2d_all_prizes`. The implementation must support these target types from the start:

### 3.1 `loto_2d_all_prizes`

- Candidate space: `"00"` to `"99"`.
- Source: last 2 digits of all 27 prize numbers.
- A number can appear multiple times in the same draw.
- Binary label: 1 if candidate appears at least once in the 27 extracted loto numbers.
- Hit count: number of times it appears in that draw.

### 3.2 `db_2cang`

- Candidate space: `"00"` to `"99"`.
- Source: last 2 digits of the special prize only.
- Binary label: 1 if candidate equals the last 2 digits of special prize.
- Hit count: 1 for the winning candidate, else 0.

### 3.3 `db_3cang`

- Candidate space: `"000"` to `"999"`.
- Source: last 3 digits of the special prize only.
- Binary label: 1 if candidate equals the last 3 digits of special prize.
- Hit count: 1 for the winning candidate, else 0.

Do not mix these target definitions. They must be explicitly passed as `target_type`.

---

## 4. ML Reality Constraint

The system must never claim guaranteed prediction or high accuracy.

Allowed language:

```text
probability ranking
statistical analysis
backtest result
baseline comparison
```

Forbidden language:

```text
guaranteed number
sure win
high accuracy guarantee
chắc chắn ra
kèo chắc
```

---

## 5. Required Implementation Phases

Implement the repo in these phases.

---

# PHASE 1 — Domain Core, Normalize, Validate, Transform

Goal: make the core XSMB data contract executable and fully tested.

Implement or update:

```text
xsmb/processing/normalize.py
xsmb/processing/validate.py
xsmb/processing/transform.py
xsmb/config.py
xsmb/database/schema.sql, only if needed for target definitions
DATA_CONTRACT.md, additive update only if target_type support is missing
MODEL_SPEC.md, additive update only if target_type support is missing
tests/test_normalize.py
tests/test_parser.py or new tests/test_transform.py
tests/test_validate.py if useful
```

Required functions/classes:

```python
PRIZE_SPECS = {
    "special": {"count": 1, "length": 5},
    "first": {"count": 1, "length": 5},
    "second": {"count": 2, "length": 5},
    "third": {"count": 6, "length": 5},
    "fourth": {"count": 4, "length": 4},
    "fifth": {"count": 6, "length": 4},
    "sixth": {"count": 3, "length": 3},
    "seventh": {"count": 4, "length": 2},
}
```

Add clean utilities such as:

```python
normalize_number(value: str, expected_length: int) -> str
extract_tail_digits(number: str, digits: int) -> str
candidate_space(target_type: str) -> list[str]
validate_draw_results(rows: list[dict]) -> None
extract_loto_2d_all_prizes(rows: list[dict]) -> list[dict]
extract_db_2cang(rows: list[dict]) -> str
extract_db_3cang(rows: list[dict]) -> str
build_target_hits(rows: list[dict], target_type: str) -> dict[str, int]
build_daily_training_labels(rows: list[dict], target_type: str) -> list[dict]
```

Expected daily label rows:

- `loto_2d_all_prizes`: 100 rows/day.
- `db_2cang`: 100 rows/day.
- `db_3cang`: 1000 rows/day.

Each label row should include at least:

```text
draw_date
target_type
candidate_number
label
hit_count
```

Tests must cover:

1. Leading zero preservation.
2. Correct extraction of last 2 and last 3 digits.
3. XSMB validates exactly 27 prize numbers.
4. Wrong prize count fails.
5. Wrong length fails.
6. `loto_2d_all_prizes` creates 100 candidates.
7. `db_2cang` creates 100 candidates.
8. `db_3cang` creates 1000 candidates.
9. Hit count works when one 2-digit number appears multiple times in 27 prizes.
10. Special prize extraction does not accidentally use other prizes.

Run:

```bash
python -m pytest tests/test_normalize.py tests/test_parser.py tests/test_features.py tests/test_backtest.py -q
```

If some listed tests do not exist yet, create/update them appropriately and run full pytest:

```bash
python -m pytest -q
```

Stop after Phase 1.

---

# PHASE 2 — SQLite Database + Repository

Only start this after approval.

Goal: persist raw HTML, normalized draw results, and target hits.

Implement/update:

```text
xsmb/database/connection.py
xsmb/database/repository.py
xsmb/database/schema.sql
tests/test_database.py
```

Required tables:

```text
raw_results
  id
  draw_date
  source_url
  raw_html
  crawled_at

 draw_results
  id
  draw_date
  prize_tier
  prize_index
  winning_number

 target_hits
  id
  draw_date
  target_type
  candidate_number
  label
  hit_count
```

Rules:

- Unique constraints should prevent duplicate draw rows.
- Re-running processing should be idempotent.
- Store all lottery numbers as TEXT.
- Repository functions should accept `Path` or config-driven DB path.

Stop after Phase 2.

---

# PHASE 3 — Scraping, Source Config, Parser

Only start this after approval.

Goal: build safe scraping and parser architecture. Do not aggressively crawl.

Implement/update:

```text
xsmb/scraping/sources.py
xsmb/scraping/crawler.py
xsmb/scraping/parser.py
tests/test_parser.py
```

Rules:

- Use timeout.
- Use retry with small backoff.
- Use clear User-Agent.
- Save raw HTML before parsing.
- Parser must be testable from static HTML fixtures.
- Add at least one sample fixture under `tests/fixtures/`.
- Do not hardcode fragile parsing without tests.

The parser output must be normalized rows:

```text
draw_date
prize_tier
prize_index
winning_number
```

Stop after Phase 3.

---

# PHASE 4 — Feature Engineering

Only start this after approval.

Goal: build leakage-safe features for all target types.

Implement/update:

```text
xsmb/features/frequency_features.py
xsmb/features/gap_features.py
xsmb/features/rolling_features.py
xsmb/features/build_dataset.py
tests/test_features.py
```

Required feature groups:

```text
freq_7
freq_14
freq_30
freq_60
freq_90
freq_180
hit_count_sum_30
current_gap
max_gap_before_target
avg_gap_before_target
days_since_last_seen
rolling_hit_rate_30
rolling_hit_rate_90
```

Hard rule:

For a row with `target_date = T`, features must only use rows where `draw_date < T`.

Add explicit tests that would fail if `draw_date == T` is included in feature calculation.

Dataset builder should support:

```python
build_feature_dataset(history_df, target_type: str, start_date=None, end_date=None, min_history_days=30)
```

Stop after Phase 4.

---

# PHASE 5 — Baselines, Metrics, Backtest

Only start this after approval.

Goal: implement baselines and rigorous walk-forward backtest.

Implement/update:

```text
xsmb/models/baseline.py
xsmb/models/evaluate.py
xsmb/models/backtest.py
tests/test_backtest.py
```

Baselines:

```text
random_uniform
frequency_30
frequency_90
gap_rank
```

Metrics:

```text
brier_score
log_loss
precision_at_k
hit_rate_at_k
avg_hits_at_k
recall_at_k
calibration_by_bucket
```

Backtest must:

- Split by time only.
- Never use random train/test split.
- Recompute features as of each target date or guarantee prebuilt features are leakage-safe.
- Produce raw prediction report and summary report.
- Work for all target types.

Stop after Phase 5.

---

# PHASE 6 — ML Train/Predict

Only start this after approval.

Goal: train baseline ML models and output probability rankings.

Implement/update:

```text
xsmb/models/train.py
xsmb/models/predict.py
xsmb/models/evaluate.py
```

Models:

```text
logistic_regression
random_forest
hist_gradient_boosting if available from sklearn
```

Rules:

- Pipelines must handle preprocessing safely.
- Calibration is required for tree models if enough data exists.
- Save model artifacts under `data/models/`.
- Prediction output must include all candidates in candidate space.
- Sort by probability descending.

Prediction output schema:

```text
target_date
target_type
candidate_number
probability
rank
selected_features/debug columns optional
```

Stop after Phase 6.

---

# PHASE 7 — CLI + FastAPI

Only start this after approval.

Goal: expose the pipeline through CLI and API.

Implement/update:

```text
app/main.py
xsmb/api/schemas.py
xsmb/api/routes.py
```

CLI commands:

```bash
python -m app.main scrape --start-date YYYY-MM-DD --end-date YYYY-MM-DD
python -m app.main process --start-date YYYY-MM-DD --end-date YYYY-MM-DD
python -m app.main build-features --target-type loto_2d_all_prizes
python -m app.main backtest --target-type loto_2d_all_prizes --model frequency_30
python -m app.main train --target-type loto_2d_all_prizes --model logistic_regression
python -m app.main predict --target-date YYYY-MM-DD --target-type db_3cang --top-k 20
```

API endpoints:

```text
GET /health
GET /targets
POST /predict
POST /backtest
```

Stop after Phase 7.

---

# PHASE 8 — Streamlit Dashboard

Only start this after approval.

Goal: simple local dashboard, not a fancy frontend.

Implement/update:

```text
xsmb/dashboard/streamlit_app.py
```

Views:

```text
latest predictions by target_type
backtest summary
probability distribution
calibration chart if report exists
top-k performance comparison
```

Stop after Phase 8.

---

## 6. Final Quality Gates

At the end of every phase, run:

```bash
python -m pytest -q
```

If formatting tools are configured, run them. If not configured, do not introduce new tooling unless necessary.

Before final completion, ensure:

1. All tests pass.
2. All generated outputs preserve leading zeros.
3. Feature generation is leakage-safe.
4. Backtest is date-based.
5. All target types work:
   - `loto_2d_all_prizes`
   - `db_2cang`
   - `db_3cang`
6. No guaranteed prediction claims exist in README/API/dashboard text.
7. `plans/CODING_PROGRESS.md` is updated.

---

## 7. Start Now

Start with **Phase 1 only**.

Do not implement Phase 2 or later yet.

