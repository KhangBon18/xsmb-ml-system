"""SQLAlchemy ORM models for the XSMB ML database."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    """Return the current UTC timestamp for ORM defaults."""
    return datetime.now(timezone.utc)


class RawPage(Base):
    """Original scraped source content retained for audit and reparse."""

    __tablename__ = "raw_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_name = Column(String(100), nullable=False)
    source_url = Column(Text, nullable=False)
    draw_date = Column(String(10), nullable=False, index=True)
    raw_html = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    checksum = Column(String(128), nullable=True, index=True)
    scraped_at = Column(DateTime, nullable=False, default=utc_now)
    parser_version = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="scraped")
    error_message = Column(Text, nullable=True)


class Draw(Base):
    """One official XSMB draw for a draw date."""

    __tablename__ = "draws"

    id = Column(Integer, primary_key=True, autoincrement=True)
    draw_date = Column(String(10), nullable=False, unique=True, index=True)
    region = Column(String(50), nullable=False, default="mien_bac")
    province = Column(String(50), nullable=False, default="XSMB")
    draw_code = Column(String(100), nullable=True)
    source_name = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default="parsed")
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    prizes = relationship(
        "Prize",
        back_populates="draw",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    targets = relationship(
        "Target",
        back_populates="draw",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Prize(Base):
    """A prize number belonging to one draw."""

    __tablename__ = "prizes"
    __table_args__ = (
        UniqueConstraint(
            "draw_id",
            "prize_tier",
            "prize_index",
            name="uq_prizes_draw_tier_index",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    draw_id = Column(Integer, ForeignKey("draws.id", ondelete="CASCADE"), nullable=False)
    prize_tier = Column(String(50), nullable=False)
    prize_index = Column(Integer, nullable=False)
    winning_number = Column(Text, nullable=False)
    number_length = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    draw = relationship("Draw", back_populates="prizes")


class Target(Base):
    """Deterministic target hits and labels generated from draw prizes."""

    __tablename__ = "targets"
    __table_args__ = (
        UniqueConstraint(
            "draw_id",
            "target_type",
            "candidate_number",
            name="uq_targets_draw_type_candidate",
        ),
        CheckConstraint("label IN (0, 1)", name="ck_targets_label_binary"),
        CheckConstraint("hit_count >= 0", name="ck_targets_hit_count_non_negative"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    draw_id = Column(Integer, ForeignKey("draws.id", ondelete="CASCADE"), nullable=False)
    draw_date = Column(String(10), nullable=False, index=True)
    target_type = Column(String(50), nullable=False, index=True)
    candidate_number = Column(Text, nullable=False)
    label = Column(Integer, nullable=False)
    hit_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    draw = relationship("Draw", back_populates="targets")


class FeatureSnapshot(Base):
    """Feature payload captured for a target date and candidate."""

    __tablename__ = "feature_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "target_date",
            "target_type",
            "candidate_number",
            "feature_version",
            name="uq_feature_snapshots_key",
        ),
        CheckConstraint("label IN (0, 1)", name="ck_feature_snapshots_label_binary"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_date = Column(String(10), nullable=False, index=True)
    target_type = Column(String(50), nullable=False, index=True)
    candidate_number = Column(Text, nullable=False)
    feature_json = Column(Text, nullable=False)
    label = Column(Integer, nullable=False)
    feature_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)


class ModelRun(Base):
    """Metadata for a training or backtest run."""

    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_name = Column(String(200), nullable=False)
    model_name = Column(String(100), nullable=False)
    target_type = Column(String(50), nullable=False, index=True)
    feature_version = Column(String(50), nullable=False)
    train_from = Column(String(10), nullable=True)
    train_to = Column(String(10), nullable=True)
    test_from = Column(String(10), nullable=True)
    test_to = Column(String(10), nullable=True)
    params_json = Column(Text, nullable=True)
    metrics_json = Column(Text, nullable=True)
    artifact_path = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    predictions = relationship("Prediction", back_populates="model_run")


class Prediction(Base):
    """Ranked model prediction for a candidate number."""

    __tablename__ = "predictions"
    __table_args__ = (
        CheckConstraint("rank >= 1", name="ck_predictions_rank_starts_at_one"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_date = Column(String(10), nullable=False, index=True)
    target_type = Column(String(50), nullable=False, index=True)
    candidate_number = Column(Text, nullable=False)
    score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    model_run_id = Column(Integer, ForeignKey("model_runs.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    model_run = relationship("ModelRun", back_populates="predictions")


def init_db(engine: Engine) -> None:
    """Create all ORM-managed database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db(engine: Engine) -> None:
    """Drop all ORM-managed database tables."""
    Base.metadata.drop_all(bind=engine)
