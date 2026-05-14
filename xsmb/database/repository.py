"""Repository classes for XSMB database read/write operations."""

from __future__ import annotations

from typing import Any, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from xsmb.config import PRIZE_SPECS, PRIZE_TIERS
from xsmb.database.models import (
    Draw,
    FeatureSnapshot,
    ModelRun,
    Prediction,
    Prize,
    RawPage,
    Target,
)
from xsmb.processing.normalize import normalize_number
from xsmb.processing.transform import build_daily_training_labels, candidate_space
from xsmb.processing.validate import validate_draw_results


class RawPageRepository:
    """Data access for raw source pages."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def insert(
        self,
        *,
        source_name: str,
        source_url: str,
        draw_date: str,
        raw_html: Optional[str] = None,
        raw_text: Optional[str] = None,
        checksum: Optional[str] = None,
        parser_version: Optional[str] = None,
        status: str = "scraped",
        error_message: Optional[str] = None,
    ) -> RawPage:
        """Insert a raw page, returning an existing row for duplicate checksums."""
        if checksum:
            existing = self.get_by_checksum(checksum)
            if existing is not None:
                return existing

        raw_page = RawPage(
            source_name=source_name,
            source_url=source_url,
            draw_date=draw_date,
            raw_html=raw_html,
            raw_text=raw_text,
            checksum=checksum,
            parser_version=parser_version,
            status=status,
            error_message=error_message,
        )
        self.session.add(raw_page)
        self.session.flush()
        return raw_page

    def get_by_checksum(self, checksum: str) -> Optional[RawPage]:
        """Return the first raw page with a checksum, if present."""
        return self.session.scalar(select(RawPage).where(RawPage.checksum == checksum))


class DrawRepository:
    """Data access for official draw rows."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_draw_date(self, draw_date: str) -> Optional[Draw]:
        """Return a draw by date."""
        return self.session.scalar(select(Draw).where(Draw.draw_date == draw_date))

    def create_or_get(
        self,
        *,
        draw_date: str,
        region: str = "mien_bac",
        province: str = "XSMB",
        draw_code: Optional[str] = None,
        source_name: Optional[str] = None,
        status: str = "parsed",
    ) -> Draw:
        """Create a draw if absent; otherwise return the existing draw."""
        existing = self.get_by_draw_date(draw_date)
        if existing is not None:
            return existing

        draw = Draw(
            draw_date=draw_date,
            region=region,
            province=province,
            draw_code=draw_code,
            source_name=source_name,
            status=status,
        )
        self.session.add(draw)
        self.session.flush()
        return draw

    def update_status(self, draw: Draw, status: str) -> Draw:
        """Update a draw status."""
        draw.status = status
        self.session.flush()
        return draw


class PrizeRepository:
    """Data access for the 27 prize rows of a draw."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_prizes(self, draw: Draw | int, rows: list[dict[str, Any]]) -> list[Prize]:
        """Save a full set of 27 validated prize rows for a draw.

        Re-saving the exact same prize rows is idempotent. Attempting to save a
        different number for an existing `(draw_id, prize_tier, prize_index)`
        raises `ValueError`.
        """
        draw_obj = self._resolve_draw(draw)
        normalized_rows = self._normalize_rows_for_draw(draw_obj, rows)
        prizes: list[Prize] = []

        for row in normalized_rows:
            existing = self._get_prize(
                draw_obj.id, row["prize_tier"], row["prize_index"]
            )
            if existing is not None:
                if (
                    existing.winning_number != row["winning_number"]
                    or existing.number_length != row["number_length"]
                ):
                    raise ValueError(
                        "Conflicting prize already exists for "
                        f"{row['prize_tier']}[{row['prize_index']}]"
                    )
                prizes.append(existing)
                continue

            prize = Prize(
                draw_id=draw_obj.id,
                prize_tier=row["prize_tier"],
                prize_index=row["prize_index"],
                winning_number=row["winning_number"],
                number_length=row["number_length"],
            )
            self.session.add(prize)
            prizes.append(prize)

        self.session.flush()
        return self._sort_prizes(prizes)

    def list_by_draw_id(self, draw_id: int) -> list[Prize]:
        """Return prizes for a draw id in XSMB prize order."""
        prizes = list(
            self.session.scalars(select(Prize).where(Prize.draw_id == draw_id)).all()
        )
        return self._sort_prizes(prizes)

    def list_by_draw_date(self, draw_date: str) -> list[Prize]:
        """Return prizes for a draw date in XSMB prize order."""
        prizes = list(
            self.session.scalars(
                select(Prize).join(Draw).where(Draw.draw_date == draw_date)
            ).all()
        )
        return self._sort_prizes(prizes)

    def _resolve_draw(self, draw: Draw | int) -> Draw:
        if isinstance(draw, Draw):
            if draw.id is None:
                self.session.flush()
            return draw

        draw_obj = self.session.get(Draw, draw)
        if draw_obj is None:
            raise ValueError(f"Draw does not exist: {draw}")
        return draw_obj

    def _normalize_rows_for_draw(
        self, draw: Draw, rows: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if any(row.get("draw_date") != draw.draw_date for row in rows):
            raise ValueError("Prize rows must use the same draw_date as the draw")

        validate_draw_results(rows)
        normalized_rows: list[dict[str, Any]] = []
        for row in rows:
            prize_tier = row["prize_tier"]
            number_length = PRIZE_SPECS[prize_tier]["length"]
            normalized_rows.append(
                {
                    "draw_date": row["draw_date"],
                    "prize_tier": prize_tier,
                    "prize_index": row["prize_index"],
                    "winning_number": normalize_number(
                        row["winning_number"], number_length
                    ),
                    "number_length": number_length,
                }
            )
        return normalized_rows

    def _get_prize(
        self, draw_id: int, prize_tier: str, prize_index: int
    ) -> Optional[Prize]:
        return self.session.scalar(
            select(Prize).where(
                Prize.draw_id == draw_id,
                Prize.prize_tier == prize_tier,
                Prize.prize_index == prize_index,
            )
        )

    @staticmethod
    def _sort_prizes(prizes: Iterable[Prize]) -> list[Prize]:
        return sorted(
            prizes,
            key=lambda prize: (PRIZE_TIERS.index(prize.prize_tier), prize.prize_index),
        )


class TargetRepository:
    """Data access for deterministic target labels generated from prizes."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def generate_and_save_targets(self, draw: Draw | int, target_type: str) -> list[Target]:
        """Generate targets from stored prizes and save them idempotently."""
        draw_obj = self._resolve_draw(draw)
        expected_count = len(candidate_space(target_type))
        existing = self.list_by_draw_id_and_target_type(draw_obj.id, target_type)
        if existing:
            if len(existing) != expected_count:
                raise ValueError(
                    f"Existing target set for {target_type!r} is incomplete: "
                    f"{len(existing)} of {expected_count}"
                )
            return existing

        prize_rows = self._draw_prize_rows(draw_obj)
        label_rows = build_daily_training_labels(prize_rows, target_type)
        targets = [
            Target(
                draw_id=draw_obj.id,
                draw_date=label_row["draw_date"],
                target_type=label_row["target_type"],
                candidate_number=label_row["candidate_number"],
                label=label_row["label"],
                hit_count=label_row["hit_count"],
            )
            for label_row in label_rows
        ]
        self.session.add_all(targets)
        self.session.flush()
        return self.list_by_draw_id_and_target_type(draw_obj.id, target_type)

    def list_by_draw_date_and_target_type(
        self, draw_date: str, target_type: str
    ) -> list[Target]:
        """Return targets for a draw date and target type."""
        return list(
            self.session.scalars(
                select(Target)
                .where(Target.draw_date == draw_date, Target.target_type == target_type)
                .order_by(Target.candidate_number)
            ).all()
        )

    def list_by_draw_id_and_target_type(
        self, draw_id: int, target_type: str
    ) -> list[Target]:
        """Return targets for a draw id and target type."""
        return list(
            self.session.scalars(
                select(Target)
                .where(Target.draw_id == draw_id, Target.target_type == target_type)
                .order_by(Target.candidate_number)
            ).all()
        )

    def _resolve_draw(self, draw: Draw | int) -> Draw:
        if isinstance(draw, Draw):
            if draw.id is None:
                self.session.flush()
            return draw

        draw_obj = self.session.get(Draw, draw)
        if draw_obj is None:
            raise ValueError(f"Draw does not exist: {draw}")
        return draw_obj

    def _draw_prize_rows(self, draw: Draw) -> list[dict[str, Any]]:
        prizes = PrizeRepository(self.session).list_by_draw_id(draw.id)
        if len(prizes) != 27:
            raise ValueError(f"Draw {draw.id} must have exactly 27 prizes")
        return [
            {
                "draw_date": draw.draw_date,
                "prize_tier": prize.prize_tier,
                "prize_index": prize.prize_index,
                "winning_number": prize.winning_number,
            }
            for prize in prizes
        ]


class FeatureSnapshotRepository:
    """Basic insert/list access for feature snapshots."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def insert(
        self,
        *,
        target_date: str,
        target_type: str,
        candidate_number: str,
        feature_json: str,
        label: int,
        feature_version: str,
    ) -> FeatureSnapshot:
        """Insert one feature snapshot row."""
        snapshot = FeatureSnapshot(
            target_date=target_date,
            target_type=target_type,
            candidate_number=candidate_number,
            feature_json=feature_json,
            label=label,
            feature_version=feature_version,
        )
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def list(
        self,
        *,
        target_date: Optional[str] = None,
        target_type: Optional[str] = None,
    ) -> list[FeatureSnapshot]:
        """List feature snapshots with optional filters."""
        statement = select(FeatureSnapshot)
        if target_date is not None:
            statement = statement.where(FeatureSnapshot.target_date == target_date)
        if target_type is not None:
            statement = statement.where(FeatureSnapshot.target_type == target_type)
        return list(
            self.session.scalars(
                statement.order_by(FeatureSnapshot.target_date, FeatureSnapshot.candidate_number)
            ).all()
        )


class ModelRunRepository:
    """Basic create/get/list access for model run metadata."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        run_name: str,
        model_name: str,
        target_type: str,
        feature_version: str,
        train_from: Optional[str] = None,
        train_to: Optional[str] = None,
        test_from: Optional[str] = None,
        test_to: Optional[str] = None,
        params_json: Optional[str] = None,
        metrics_json: Optional[str] = None,
        artifact_path: Optional[str] = None,
    ) -> ModelRun:
        """Create a model run metadata row."""
        run = ModelRun(
            run_name=run_name,
            model_name=model_name,
            target_type=target_type,
            feature_version=feature_version,
            train_from=train_from,
            train_to=train_to,
            test_from=test_from,
            test_to=test_to,
            params_json=params_json,
            metrics_json=metrics_json,
            artifact_path=artifact_path,
        )
        self.session.add(run)
        self.session.flush()
        return run

    def get(self, model_run_id: int) -> Optional[ModelRun]:
        """Return a model run by id."""
        return self.session.get(ModelRun, model_run_id)

    def list(self, *, target_type: Optional[str] = None) -> list[ModelRun]:
        """List model runs with an optional target type filter."""
        statement = select(ModelRun)
        if target_type is not None:
            statement = statement.where(ModelRun.target_type == target_type)
        return list(
            self.session.scalars(statement.order_by(ModelRun.created_at, ModelRun.id)).all()
        )


class PredictionRepository:
    """Basic save/list access for ranked predictions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_predictions(
        self,
        *,
        prediction_date: str,
        target_type: str,
        predictions: list[dict[str, Any]],
        model_run_id: Optional[int] = None,
    ) -> list[Prediction]:
        """Save ranked predictions for one prediction date and target type."""
        rows = [
            Prediction(
                prediction_date=prediction_date,
                target_type=target_type,
                candidate_number=row["candidate_number"],
                score=row["score"],
                rank=row["rank"],
                model_run_id=row.get("model_run_id", model_run_id),
            )
            for row in predictions
        ]
        self.session.add_all(rows)
        self.session.flush()
        return rows

    def list_top_k(
        self,
        *,
        prediction_date: str,
        target_type: str,
        k: int,
        model_run_id: Optional[int] = None,
    ) -> list[Prediction]:
        """Return top-k predictions ordered by ascending rank."""
        if k <= 0:
            raise ValueError("k must be positive")

        statement = select(Prediction).where(
            Prediction.prediction_date == prediction_date,
            Prediction.target_type == target_type,
        )
        if model_run_id is not None:
            statement = statement.where(Prediction.model_run_id == model_run_id)
        return list(
            self.session.scalars(statement.order_by(Prediction.rank).limit(k)).all()
        )
