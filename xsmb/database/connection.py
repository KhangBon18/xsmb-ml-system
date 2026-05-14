"""SQLAlchemy database connection helpers for the XSMB system."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from xsmb.config import DATABASE_URL_ENV_VAR, DEFAULT_DATABASE_URL


def get_database_url() -> str:
    """Resolve the database URL from the environment or the SQLite default."""
    database_url = os.getenv(DATABASE_URL_ENV_VAR)
    if database_url is None or database_url.strip() == "":
        return DEFAULT_DATABASE_URL
    return database_url.strip()


def create_engine_from_url(database_url: Optional[str] = None) -> Engine:
    """Create a SQLAlchemy engine and prepare SQLite parent directories.

    Args:
        database_url: Optional SQLAlchemy database URL. When omitted, the value
            comes from the `DATABASE_URL` environment variable, with a fallback
            to `sqlite:///data/xsmb.sqlite3`.

    Returns:
        A SQLAlchemy Engine configured for future-style usage.
    """
    resolved_url = database_url.strip() if database_url else get_database_url()
    _ensure_sqlite_parent_directory(resolved_url)

    connect_args = {}
    if make_url(resolved_url).get_backend_name() == "sqlite":
        connect_args["check_same_thread"] = False

    engine = create_engine(resolved_url, future=True, connect_args=connect_args)
    if make_url(resolved_url).get_backend_name() == "sqlite":
        _enable_sqlite_foreign_keys(engine)

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a SQLAlchemy session factory bound to an engine."""
    return sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )


def get_session(database_url: Optional[str] = None) -> Session:
    """Create a new SQLAlchemy session for the resolved database URL."""
    engine = create_engine_from_url(database_url)
    session_factory = create_session_factory(engine)
    return session_factory()


def _ensure_sqlite_parent_directory(database_url: str) -> None:
    """Create parent directories for file-based SQLite URLs."""
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        return

    database_path = url.database
    if not database_path or database_path == ":memory:":
        return

    Path(database_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


def _enable_sqlite_foreign_keys(engine: Engine) -> None:
    """Enable SQLite foreign-key checks on every new DB-API connection."""

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
