# AGENTS.md

## Project

This is a Python system for collecting, normalizing, analyzing, backtesting, and predicting probability rankings for XSMB 2-digit loto numbers.

The system is for statistical analysis only. It must not claim guaranteed lottery prediction.

## Core Problem

For each target date, predict the probability that each 2-digit number from "00" to "99" appears at least once in the 27 XSMB loto entries of that date.

Each training row is:

- target_date
- number: "00" to "99"
- features built only from dates before target_date
- label: 1 if number appears in target_date, else 0

## Critical Rules

1. Never use future data when building features.
2. Never use random train/test split for model evaluation. Always split by date.
3. All lottery numbers must be stored as strings, not integers.
4. Leading zeros must be preserved. Examples: "00", "01", "05", "09".
5. Each XSMB draw date must produce exactly 27 two-digit loto entries.
6. Raw crawled data must be saved before parsing.
7. Every parser and feature function must have tests.
8. Do not add unnecessary frameworks.
9. Do not create a frontend before data, validation, baseline, and backtest are working.
10. Do not make claims that the model can guarantee winning.

## Preferred Stack

- Python
- SQLite for MVP
- pandas
- requests or httpx
- BeautifulSoup or lxml
- scikit-learn
- FastAPI
- Streamlit
- pytest

## Repository Layout

Use the existing repository structure. Do not rename top-level folders unless explicitly requested.

Expected structure:

xsmb-ml-system/
README.md
pyproject.toml
.env.example
docker-compose.yml

app/
main.py

xsmb/
config.py

    scraping/
      sources.py
      crawler.py
      parser.py

    database/
      connection.py
      schema.sql
      repository.py

    processing/
      normalize.py
      validate.py
      transform.py

    features/
      build_dataset.py
      rolling_features.py
      gap_features.py
      frequency_features.py

    models/
      baseline.py
      train.py
      predict.py
      evaluate.py
      backtest.py

    api/
      routes.py
      schemas.py

    dashboard/
      streamlit_app.py

data/
raw/
processed/
models/
reports/

tests/
test_parser.py
test_normalize.py
test_features.py
test_backtest.py

## Coding Style

- Write small functions.
- Add type hints.
- Add docstrings for public functions.
- Prefer explicit errors over silent failures.
- Keep functions deterministic where possible.
- Avoid hidden global state.
- Use pathlib instead of raw string paths.
- Use logging instead of print in library modules.
- Scripts may print CLI output.

## Testing

Use pytest.

Every important module should have tests:

- parser
- validator
- two-digit extraction
- feature builder
- no-future-data guard
- baseline ranking
- backtest metrics

## Data Safety

When scraping:

- Use timeout.
- Use retry.
- Use a clear User-Agent.
- Respect rate limits.
- Cache raw responses.
- Do not aggressively crawl.

## Definition of Done

A task is done only when:

1. Code runs.
2. Tests pass.
3. Existing tests are not broken.
4. No future leakage is introduced.
5. Leading zeros are preserved.
6. The output format matches the agreed data contract.
