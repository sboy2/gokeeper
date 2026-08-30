"""Web-layer tests for the FastAPI shell (§11.2)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from gokeeper.db.connection import write_lock
from web import app as web_app

_MIGRATION_FILE_PATTERN = re.compile(r"^(\d+)_.+\.sql$")


def _latest_migration_version(migrations_dir: Path) -> int:
    """Return the highest NNN prefix among ``NNN_*.sql`` files."""
    versions = [
        int(match.group(1))
        for path in migrations_dir.iterdir()
        if path.is_file()
        and (match := _MIGRATION_FILE_PATTERN.match(path.name)) is not None
    ]
    assert versions, "repo migrations/ must contain at least one NNN_*.sql file"
    return max(versions)


def test_get_root_returns_200(client: TestClient) -> None:
    """GET / returns 200 with the stub placeholder body."""
    response = client.get("/")
    assert response.status_code == 200
    assert "gokeeper" in response.text


def test_lifespan_opens_migrated_connection(
    client: TestClient,
    app: FastAPI,
    migrations_dir: Path,
    gokeeper_data_dir: Path,
) -> None:
    """Lifespan opens a migrated SQLite connection under the isolated data dir."""
    client.get("/")

    conn = app.state.conn
    expected_version = _latest_migration_version(migrations_dir)

    version_row = conn.execute("PRAGMA user_version").fetchone()
    assert version_row is not None
    assert int(version_row[0]) == expected_version

    database_rows = conn.execute("PRAGMA database_list").fetchall()
    main_database = next(row for row in database_rows if row["name"] == "main")
    assert Path(main_database["file"]).resolve().is_relative_to(
        gokeeper_data_dir.resolve()
    )

    assert app.state.write_lock is write_lock


def test_main_binds_localhost_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """main() starts Uvicorn on 127.0.0.1:8000 only."""
    captured: dict[str, object] = {}

    def fake_run(*args: object, **kwargs: object) -> None:
        captured["args"] = args
        captured.update(kwargs)

    monkeypatch.setattr(web_app.uvicorn, "run", fake_run)

    web_app.main()

    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 8000
