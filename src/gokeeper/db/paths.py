"""Resolve the application data directory and SQLite database path.

Precedence for the data directory (§7.1):

1. ``GOKEEPER_DATA_DIR`` environment variable
2. ``data_dir`` in the platformdirs config file
3. ``platformdirs.user_data_dir`` with ``appauthor=False``
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "gokeeper"


def data_dir() -> Path:
    """Resolve the directory that holds the SQLite database and backups.

    Checks ``GOKEEPER_DATA_DIR``, then optional ``config.toml`` under the
    platform config directory, then the platformdirs user data directory.
    Tildes in env and config values are expanded. Directories are not created.

    Returns
    -------
    Path
        Absolute or user-expanded path to the data directory.
    """
    if env := os.environ.get("GOKEEPER_DATA_DIR"):
        return Path(env).expanduser()

    config_path = Path(user_config_dir(APP_NAME, appauthor=False)) / "config.toml"
    if config_path.is_file():
        with config_path.open("rb") as file_handle:
            if custom := tomllib.load(file_handle).get("data_dir"):
                return Path(custom).expanduser()

    return Path(user_data_dir(APP_NAME, appauthor=False))


def db_path() -> Path:
    """Ensure the data and backups directories exist and return the DB file path.

    Creates ``data_dir()`` and ``data_dir() / "backups"`` if missing.

    Returns
    -------
    Path
        Path to ``gokeeper.sqlite`` under the resolved data directory.
    """
    resolved_data_dir = data_dir()
    resolved_data_dir.mkdir(parents=True, exist_ok=True)
    (resolved_data_dir / "backups").mkdir(exist_ok=True)
    return resolved_data_dir / "gokeeper.sqlite"
