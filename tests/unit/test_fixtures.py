"""Unit tests for shared pytest fixtures (§11.2)."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from gokeeper.db import paths
from gokeeper.db.migrations import run_migrations

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


def test_gokeeper_data_dir_fixture_isolates_paths(
    tmp_path: Path, gokeeper_data_dir: Path
) -> None:
    """Autouse fixture points data_dir/db_path at a temporary directory under tmp_path."""
    assert paths.data_dir() == gokeeper_data_dir
    assert gokeeper_data_dir.is_relative_to(tmp_path)

    resolved_db_path = paths.db_path()
    assert resolved_db_path.parent == gokeeper_data_dir
    assert resolved_db_path.name == "gokeeper.sqlite"
    assert resolved_db_path.is_relative_to(tmp_path)


def test_migrated_db_connection_applies_migrations(
    migrated_db_connection: sqlite3.Connection,
    migrations_dir: Path,
    gokeeper_data_dir: Path,
) -> None:
    """Fixture applies the full repo migration chain under the isolated data dir.

    Asserts behavior that stays true as ``001_init.sql`` grows or later
    ``NNN_*.sql`` files are added: ``user_version`` matches the latest
    migration number, the DB file lives under the temp data dir, and a
    second ``run_migrations`` is a no-op.
    """
    expected_version = _latest_migration_version(migrations_dir)

    version_row = migrated_db_connection.execute("PRAGMA user_version").fetchone()
    assert version_row is not None
    assert int(version_row[0]) == expected_version

    database_rows = migrated_db_connection.execute("PRAGMA database_list").fetchall()
    main_database = next(row for row in database_rows if row["name"] == "main")
    assert Path(main_database["file"]).resolve().is_relative_to(
        gokeeper_data_dir.resolve()
    )

    assert run_migrations(migrated_db_connection, migrations_dir) == expected_version
