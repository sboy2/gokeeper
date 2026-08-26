"""SQLite connection setup and shared write lock (§7.2).

``connect`` opens a connection suitable for sharing across Uvicorn worker
threads. Callers must hold ``write_lock`` around write transactions on that
shared connection; the connection itself is never stored as a module global.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

write_lock = threading.Lock()


def connect(path: str | Path) -> sqlite3.Connection:
    """Open a SQLite connection with gokeeper PRAGMAs and row factory.

    Parameters
    ----------
    path : str | Path
        Database file path, or ``:memory:`` for an in-memory database.

    Returns
    -------
    sqlite3.Connection
        Connection with ``check_same_thread=False``, ``sqlite3.Row`` rows,
        WAL journal mode (where applicable), foreign keys on, and
        ``synchronous=NORMAL``.

    Notes
    -----
    Hold ``write_lock`` around write transactions when the connection is
    shared across threads.
    """
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn
