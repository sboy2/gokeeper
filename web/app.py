"""FastAPI application factory and console entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from gokeeper.db.connection import connect, write_lock
from gokeeper.db.migrations import run_migrations
from gokeeper.db.paths import db_path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def _default_migrations_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "migrations"


def create_app(migrations_dir: Path | None = None) -> FastAPI:
    """Create a FastAPI application with database lifespan wiring.

    Opens SQLite at ``db_path()``, applies pending migrations, and stores
    the connection and shared write lock on ``app.state``. No module-level
    app singleton — each caller gets a fresh instance for tests or Uvicorn.

    Parameters
    ----------
    migrations_dir : Path | None, optional
        Directory of ``NNN_*.sql`` migration files. Defaults to the
        repository ``migrations/`` next to the ``web`` package.

    Returns
    -------
    FastAPI
        Configured application with stub ``GET /`` route.
    """
    resolved_migrations_dir = migrations_dir or _default_migrations_dir()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        conn = connect(db_path())
        run_migrations(conn, resolved_migrations_dir)
        app.state.conn = conn
        app.state.write_lock = write_lock
        try:
            yield
        finally:
            conn.close()

    application = FastAPI(lifespan=lifespan)

    @application.get("/")
    def read_root() -> PlainTextResponse:
        return PlainTextResponse("gokeeper")

    return application


def main() -> None:
    """Start Uvicorn bound to localhost only.

    Console entrypoint for ``uv run gokeeper``. Listens on ``127.0.0.1:8000``.
    """
    uvicorn.run(
        create_app(),
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
    )
