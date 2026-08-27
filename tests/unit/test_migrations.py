"""Unit tests for user_version migrations runner (§7.4)."""

from __future__ import annotations

from pathlib import Path

from gokeeper.db.connection import connect
from gokeeper.db.migrations import run_migrations


def _user_version(conn) -> int:
    row = conn.execute("PRAGMA user_version").fetchone()
    assert row is not None
    return int(row[0])


def _table_exists(conn, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def test_run_migrations_applies_stub_and_sets_user_version(
    migrations_dir: Path,
) -> None:
    """Repo stub migration creates app_meta and sets user_version to 1."""
    conn = connect(":memory:")
    try:
        version = run_migrations(conn, migrations_dir)
        assert version == 1
        assert _user_version(conn) == 1
        assert _table_exists(conn, "app_meta")
    finally:
        conn.close()


def test_run_migrations_second_apply_is_noop(migrations_dir: Path) -> None:
    """Re-running migrations leaves user_version unchanged and does not error."""
    conn = connect(":memory:")
    try:
        first = run_migrations(conn, migrations_dir)
        second = run_migrations(conn, migrations_dir)
        assert first == 1
        assert second == 1
        assert _user_version(conn) == 1
        assert _table_exists(conn, "app_meta")
    finally:
        conn.close()

def test_run_migrations_applies_pending_files_in_order(tmp_path: Path) -> None:
    """Multiple numbered SQL files apply in order and advance user_version."""
    (tmp_path / "001_a.sql").write_text(
        "CREATE TABLE table_a (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )
    (tmp_path / "002_b.sql").write_text(
        "CREATE TABLE table_b (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )
    conn = connect(":memory:")
    try:
        version = run_migrations(conn, tmp_path)
        assert version == 2
        assert _user_version(conn) == 2
        assert _table_exists(conn, "table_a")
        assert _table_exists(conn, "table_b")
    finally:
        conn.close()


def test_run_migrations_skips_already_applied(tmp_path: Path) -> None:
    """Only migrations newer than current user_version are applied."""
    (tmp_path / "001_a.sql").write_text(
        "CREATE TABLE table_a (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )
    conn = connect(":memory:")
    try:
        assert run_migrations(conn, tmp_path) == 1
        assert _table_exists(conn, "table_a")

        (tmp_path / "002_b.sql").write_text(
            "CREATE TABLE table_b (id INTEGER PRIMARY KEY);\n",
            encoding="utf-8",
        )
        assert run_migrations(conn, tmp_path) == 2
        assert _user_version(conn) == 2
        assert _table_exists(conn, "table_b")
    finally:
        conn.close()


def test_run_migrations_ignores_non_migration_entries(tmp_path: Path) -> None:
    """Non-matching names and subdirectories are ignored during discovery."""
    (tmp_path / "001_ok.sql").write_text(
        "CREATE TABLE ok_table (id INTEGER PRIMARY KEY);\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("not a migration\n", encoding="utf-8")
    (tmp_path / "notes").mkdir()
    conn = connect(":memory:")
    try:
        assert run_migrations(conn, tmp_path) == 1
        assert _table_exists(conn, "ok_table")
    finally:
        conn.close()


def test_run_migrations_missing_directory_is_noop(tmp_path: Path) -> None:
    """A missing migrations directory leaves user_version at 0."""
    missing = tmp_path / "does-not-exist"
    conn = connect(":memory:")
    try:
        assert run_migrations(conn, missing) == 0
        assert _user_version(conn) == 0
    finally:
        conn.close()
