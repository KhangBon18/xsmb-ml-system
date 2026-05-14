-- XSMB ML System SQLite schema documentation.
-- SQLAlchemy ORM models in xsmb/database/models.py are the source of truth.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS raw_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name VARCHAR(100) NOT NULL,
    source_url TEXT NOT NULL,
    draw_date VARCHAR(10) NOT NULL,
    raw_html TEXT,
    raw_text TEXT,
    checksum VARCHAR(128),
    scraped_at DATETIME NOT NULL,
    parser_version VARCHAR(50),
    status VARCHAR(50) NOT NULL,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS ix_raw_pages_draw_date ON raw_pages(draw_date);
CREATE INDEX IF NOT EXISTS ix_raw_pages_checksum ON raw_pages(checksum);

CREATE TABLE IF NOT EXISTS draws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date VARCHAR(10) NOT NULL UNIQUE,
    region VARCHAR(50) NOT NULL DEFAULT 'mien_bac',
    province VARCHAR(50) NOT NULL DEFAULT 'XSMB',
    draw_code VARCHAR(100),
    source_name VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'parsed',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_draws_draw_date ON draws(draw_date);

CREATE TABLE IF NOT EXISTS prizes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_id INTEGER NOT NULL,
    prize_tier VARCHAR(50) NOT NULL,
    prize_index INTEGER NOT NULL,
    winning_number TEXT NOT NULL,
    number_length INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    CONSTRAINT uq_prizes_draw_tier_index UNIQUE (draw_id, prize_tier, prize_index),
    FOREIGN KEY(draw_id) REFERENCES draws(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_id INTEGER NOT NULL,
    draw_date VARCHAR(10) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    candidate_number TEXT NOT NULL,
    label INTEGER NOT NULL,
    hit_count INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    CONSTRAINT uq_targets_draw_type_candidate UNIQUE (draw_id, target_type, candidate_number),
    CONSTRAINT ck_targets_label_binary CHECK (label IN (0, 1)),
    CONSTRAINT ck_targets_hit_count_non_negative CHECK (hit_count >= 0),
    FOREIGN KEY(draw_id) REFERENCES draws(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_targets_draw_date ON targets(draw_date);
CREATE INDEX IF NOT EXISTS ix_targets_target_type ON targets(target_type);

CREATE TABLE IF NOT EXISTS feature_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_date VARCHAR(10) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    candidate_number TEXT NOT NULL,
    feature_json TEXT NOT NULL,
    label INTEGER NOT NULL,
    feature_version VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    CONSTRAINT uq_feature_snapshots_key UNIQUE (
        target_date,
        target_type,
        candidate_number,
        feature_version
    ),
    CONSTRAINT ck_feature_snapshots_label_binary CHECK (label IN (0, 1))
);

CREATE INDEX IF NOT EXISTS ix_feature_snapshots_target_date ON feature_snapshots(target_date);
CREATE INDEX IF NOT EXISTS ix_feature_snapshots_target_type ON feature_snapshots(target_type);

CREATE TABLE IF NOT EXISTS model_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_name VARCHAR(200) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    feature_version VARCHAR(50) NOT NULL,
    train_from VARCHAR(10),
    train_to VARCHAR(10),
    test_from VARCHAR(10),
    test_to VARCHAR(10),
    params_json TEXT,
    metrics_json TEXT,
    artifact_path TEXT,
    created_at DATETIME NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_model_runs_target_type ON model_runs(target_type);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_date VARCHAR(10) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    candidate_number TEXT NOT NULL,
    score FLOAT NOT NULL,
    rank INTEGER NOT NULL,
    model_run_id INTEGER,
    created_at DATETIME NOT NULL,
    CONSTRAINT ck_predictions_rank_starts_at_one CHECK (rank >= 1),
    FOREIGN KEY(model_run_id) REFERENCES model_runs(id)
);

CREATE INDEX IF NOT EXISTS ix_predictions_prediction_date ON predictions(prediction_date);
CREATE INDEX IF NOT EXISTS ix_predictions_target_type ON predictions(target_type);
