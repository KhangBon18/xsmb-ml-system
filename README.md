# XSMB ML System

Machine Learning system for predicting and analyzing XSMB (Northern Vietnam Lottery) results.

## Project Structure

- `app/`: Application entry points.
- `xsmb/`: Core logic package.
  - `scraping/`: Data collection from various sources.
  - `database/`: Database connection and repository pattern.
  - `processing/`: Data normalization and validation.
  - `features/`: Feature engineering (rolling, gap, frequency features).
  - `models/`: Training, prediction, and evaluation logic.
  - `api/`: FastAPI routes and schemas.
  - `dashboard/`: Streamlit dashboard for visualization.
- `data/`: Data storage (raw, processed, models, reports).
- `tests/`: Unit and integration tests.

## Setup

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in the details.
3. Install dependencies: `pip install -e .`
4. Run the system using Docker: `docker-compose up`
