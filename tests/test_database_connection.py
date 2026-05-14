"""Tests for Phase 2A database connection configuration."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from xsmb.config import DEFAULT_DATABASE_URL
from xsmb.database.connection import (
    create_engine_from_url,
    create_session_factory,
    get_database_url,
    get_session,
)


def test_get_database_url_uses_sqlite_default_when_env_missing(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert get_database_url() == DEFAULT_DATABASE_URL
    assert get_database_url() == "sqlite:///data/xsmb.sqlite3"


def test_get_database_url_uses_environment_override(monkeypatch, tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'override.sqlite3'}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    assert get_database_url() == database_url


def test_temporary_sqlite_database_can_connect(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'test.sqlite3'}"
    engine = create_engine_from_url(database_url)

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1


def test_in_memory_sqlite_database_can_connect() -> None:
    engine = create_engine_from_url("sqlite:///:memory:")

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1


def test_file_based_sqlite_creates_parent_directory(tmp_path: Path) -> None:
    database_path = tmp_path / "nested" / "db" / "xsmb.sqlite3"
    database_url = f"sqlite:///{database_path}"

    assert not database_path.parent.exists()
    engine = create_engine_from_url(database_url)

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1

    assert database_path.parent.exists()


def test_session_factory_and_get_session_work_with_temp_sqlite(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'session.sqlite3'}"
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1

    with get_session(database_url) as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1


def test_default_database_file_is_not_touched_by_tests(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)

    default_path = Path("data/xsmb.sqlite3")
    assert get_database_url() == DEFAULT_DATABASE_URL
    assert not default_path.exists()
