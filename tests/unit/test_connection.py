"""Unit tests for SQLite connect, PRAGMAs, and write_lock (§7.2)."""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from gokeeper.db import connection


def test_connect_sets_row_factory() -> None:
    """connect sets row_factory so rows support name-based access."""
    conn = connection.connect(":memory:")
    try:
        assert conn.row_factory is sqlite3.Row
        conn.execute("CREATE TABLE sample (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO sample (id, name) VALUES (1, 'pikachu')")
        row = conn.execute("SELECT id, name FROM sample").fetchone()
        assert row is not None
        assert row["name"] == "pikachu"
        assert row["id"] == 1
    finally:
        conn.close()


def test_connect_enables_foreign_keys_memory() -> None:
    """foreign_keys PRAGMA is ON for an in-memory connection."""
    conn = connection.connect(":memory:")
    try:
        foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()
        assert foreign_keys is not None
        assert foreign_keys[0] == 1
    finally:
        conn.close()


def test_connect_sets_wal_and_synchronous_on_file(tmp_path: Path) -> None:
    """Temp-file DB uses WAL journal_mode and NORMAL synchronous."""
    db_file = tmp_path / "test.sqlite"
    conn = connection.connect(db_file)
    try:
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()
        synchronous = conn.execute("PRAGMA synchronous").fetchone()
        assert journal_mode is not None
        assert synchronous is not None
        assert journal_mode[0].lower() == "wal"
        assert synchronous[0] == 1  # NORMAL
        foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()
        assert foreign_keys is not None
        assert foreign_keys[0] == 1
    finally:
        conn.close()


def test_write_lock_serializes_two_writers() -> None:
    """Two threads holding write_lock do not interleave their critical sections."""
    events: list[int] = []
    barrier = threading.Barrier(2)

    def writer(writer_id: int) -> None:
        barrier.wait()
        with connection.write_lock:
            events.append(writer_id)
            time.sleep(0.05)
            events.append(writer_id)

    threads = [
        threading.Thread(target=writer, args=(1,)),
        threading.Thread(target=writer, args=(2,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert events in ([1, 1, 2, 2], [2, 2, 1, 1])
