"""Shared pytest fixtures for isolating gokeeper data and databases.

Autouse ``gokeeper_data_dir`` ensures every test points ``GOKEEPER_DATA_DIR``
at a temporary directory so the suite never touches the developer's real
database (§11.2 / CONTRIBUTING). Request ``migrated_db_connection`` when a
test needs an open, migrated SQLite connection under that temp dir. Web tests
use ``app`` and ``client`` for a fresh FastAPI instance with lifespan started.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gokeeper.db.connection import connect
from gokeeper.db.migrations import run_migrations
from gokeeper.db.paths import db_path
from web.app import create_app


@pytest.fixture
def migrations_dir() -> Path:
    """Return the repository ``migrations/`` directory.

    Returns
    -------
    Path
        Absolute path to the committed SQL migration files.
    """
    return Path(__file__).resolve().parent.parent / "migrations"


@pytest.fixture(autouse=True)
def gokeeper_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    """Point ``GOKEEPER_DATA_DIR`` at a per-test temporary subdirectory.

    Applied automatically to every test. Path-resolution tests may still
    override the env var via ``monkeypatch`` to assert precedence.

    Parameters
    ----------
    tmp_path : Path
        Pytest per-test temporary directory.
    monkeypatch : pytest.MonkeyPatch
        Used to set ``GOKEEPER_DATA_DIR`` for the duration of the test.

    Returns
    -------
    Path
        The temporary data directory (``tmp_path / "gokeeper-data"``).
    """
    data = tmp_path / "gokeeper-data"
    monkeypatch.setenv("GOKEEPER_DATA_DIR", str(data))
    return data


@pytest.fixture
def migrated_db_connection(
    gokeeper_data_dir: Path, migrations_dir: Path
) -> Iterator[sqlite3.Connection]:
    """Open a migrated SQLite database under the isolated data directory.

    Creates the DB via ``db_path()``, applies repo migrations, and yields the
    connection. Closes the connection on teardown. Depends on the autouse
    data-dir fixture so the file never lands in the developer's real data dir.

    Parameters
    ----------
    gokeeper_data_dir : Path
        Isolated data directory (ensures env override is active).
    migrations_dir : Path
        Repository migrations directory.

    Yields
    ------
    sqlite3.Connection
        Open connection with stub (or later full) migrations applied.
    """
    resolved_db_path = db_path()
    assert resolved_db_path.parent == gokeeper_data_dir
    conn = connect(resolved_db_path)
    try:
        run_migrations(conn, migrations_dir)
        yield conn
    finally:
        conn.close()


@pytest.fixture
def app(migrations_dir: Path) -> FastAPI:
    """Return a fresh FastAPI application for web-layer tests.

    Each test gets a new app instance so lifespan opens a separate database
    connection. Passes the repository ``migrations_dir`` explicitly.

    Parameters
    ----------
    migrations_dir : Path
        Repository migrations directory.

    Returns
    -------
    FastAPI
        Application factory result without a started lifespan.
    """
    return create_app(migrations_dir=migrations_dir)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Yield a TestClient with lifespan startup and shutdown run.

    Uses ``with TestClient(app)`` so startup migrations and connection setup
    run before the test and the connection closes on teardown.

    Parameters
    ----------
    app : FastAPI
        Application under test.

    Yields
    ------
    TestClient
        HTTP client bound to the application lifespan.
    """
    with TestClient(app) as test_client:
        yield test_client
