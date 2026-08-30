"""Apply linear SQL migrations via ``PRAGMA user_version`` (§7.4)."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

_MIGRATION_FILE_PATTERN = re.compile(r"^(\d+)_.+\.sql$")


def run_migrations(conn: sqlite3.Connection, migrations_dir: Path) -> int:
    """Apply pending numbered SQL files and advance ``user_version``.

    Discovers ``NNN_*.sql`` files under ``migrations_dir``, sorts by the
    integer prefix, and applies each file with ``N`` greater than the
    current ``user_version``. Each file runs in its own transaction; on
    success ``user_version`` is set to ``N``. Already-applied files are
    skipped, so a second call is a no-op.

    Parameters
    ----------
    conn : sqlite3.Connection
        Open database connection (callers should enable foreign keys).
    migrations_dir : Path
        Directory containing numbered ``.sql`` migration files.

    Returns
    -------
    int
        Final ``user_version`` after applying any pending migrations.
    """
    current_version = _read_user_version(conn)
    pending_migrations = [
        (version, path)
        for version, path in _discover_migrations(migrations_dir)
        if version > current_version
    ]

    for version, path in pending_migrations:
        _apply_migration(conn, version, path)
        current_version = version

    return current_version


def _read_user_version(conn: sqlite3.Connection) -> int:
    row = conn.execute("PRAGMA user_version").fetchone()
    assert row is not None  # PRAGMA user_version always returns one row
    return int(row[0])


def _discover_migrations(migrations_dir: Path) -> list[tuple[int, Path]]:
    discovered: list[tuple[int, Path]] = []
    if not migrations_dir.is_dir():
        return discovered

    for path in migrations_dir.iterdir():
        if not path.is_file():
            continue
        match = _MIGRATION_FILE_PATTERN.match(path.name)
        if match is None:
            continue
        discovered.append((int(match.group(1)), path))

    discovered.sort(key=lambda item: item[0])
    return discovered


def _apply_migration(
    conn: sqlite3.Connection, version: int, path: Path
) -> None:
    # executescript issues a COMMIT before running, so the migration SQL and
    # user_version bump must share one explicit transaction inside the script.
    sql_body = path.read_text(encoding="utf-8")
    script = (
        f"BEGIN;\n{sql_body}\nPRAGMA user_version = {version};\nCOMMIT;\n"
    )
    conn.executescript(script)
