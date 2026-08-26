"""Unit tests for data_dir / db_path resolution (§7.1 / §11.1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from gokeeper.db import paths


def _mock_user_config_dir(
    monkeypatch: pytest.MonkeyPatch, config_dir: Path
) -> None:
    """Point user_config_dir at a temp directory."""

    def fake_user_config_dir(
        appname: str,
        appauthor: str | bool | None = None,
        *args: object,
        **kwargs: object,
    ) -> str:
        assert appname == paths.APP_NAME
        assert appauthor is False
        return str(config_dir)

    monkeypatch.setattr(paths, "user_config_dir", fake_user_config_dir)


def _mock_user_data_dir(
    monkeypatch: pytest.MonkeyPatch, data_dir_path: Path
) -> None:
    """Point user_data_dir at a fixed platform-default path."""

    def fake_user_data_dir(
        appname: str,
        appauthor: str | bool | None = None,
        *args: object,
        **kwargs: object,
    ) -> str:
        assert appname == paths.APP_NAME
        assert appauthor is False
        return str(data_dir_path)

    monkeypatch.setattr(paths, "user_data_dir", fake_user_data_dir)


def _write_config(config_dir: Path, contents: str) -> Path:
    """Write config.toml under config_dir and return its path."""
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.toml"
    config_path.write_text(contents, encoding="utf-8")
    return config_path


def test_data_dir_env_wins_over_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GOKEEPER_DATA_DIR beats config.toml when both are set."""
    env_dir = tmp_path / "from-env"
    config_dir = tmp_path / "config"
    platform_dir = tmp_path / "platform"
    _write_config(config_dir, f'data_dir = "{tmp_path / "from-config"}"\n')
    _mock_user_config_dir(monkeypatch, config_dir)
    _mock_user_data_dir(monkeypatch, platform_dir)
    monkeypatch.setenv("GOKEEPER_DATA_DIR", str(env_dir))

    assert paths.data_dir() == env_dir


def test_data_dir_config_wins_over_platform_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """config.toml data_dir beats the platformdirs default when env is unset."""
    config_override = tmp_path / "from-config"
    config_dir = tmp_path / "config"
    platform_dir = tmp_path / "platform"
    _write_config(config_dir, f'data_dir = "{config_override}"\n')
    _mock_user_config_dir(monkeypatch, config_dir)
    _mock_user_data_dir(monkeypatch, platform_dir)
    monkeypatch.delenv("GOKEEPER_DATA_DIR", raising=False)

    assert paths.data_dir() == config_override


def test_data_dir_platform_default_when_no_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With no env and no config file, use user_data_dir."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    platform_dir = tmp_path / "platform"
    _mock_user_config_dir(monkeypatch, config_dir)
    _mock_user_data_dir(monkeypatch, platform_dir)
    monkeypatch.delenv("GOKEEPER_DATA_DIR", raising=False)

    assert paths.data_dir() == platform_dir


def test_data_dir_expands_tilde_in_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """~ in GOKEEPER_DATA_DIR expands via Path.expanduser()."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    # On Windows expanduser also checks USERPROFILE
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    monkeypatch.setenv("GOKEEPER_DATA_DIR", "~/gokeeper-env-data")

    assert paths.data_dir() == fake_home / "gokeeper-env-data"


def test_data_dir_expands_tilde_in_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """~ in config.toml data_dir expands via Path.expanduser()."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("USERPROFILE", str(fake_home))
    config_dir = tmp_path / "config"
    _write_config(config_dir, 'data_dir = "~/gokeeper-cfg-data"\n')
    _mock_user_config_dir(monkeypatch, config_dir)
    _mock_user_data_dir(monkeypatch, tmp_path / "platform")
    monkeypatch.delenv("GOKEEPER_DATA_DIR", raising=False)

    assert paths.data_dir() == fake_home / "gokeeper-cfg-data"


def test_data_dir_passes_appauthor_false_windows_style(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """appauthor=False omits the author segment on a Windows-style path."""
    author_segment = "SomeAuthor"

    def fake_user_data_dir(
        appname: str,
        appauthor: str | bool | None = None,
        *args: object,
        **kwargs: object,
    ) -> str:
        assert appname == paths.APP_NAME
        base = r"C:\Users\test\AppData\Local"
        if appauthor is False or appauthor is None:
            return rf"{base}\gokeeper"
        return rf"{base}\{author_segment}\gokeeper"

    def fake_user_config_dir(
        appname: str,
        appauthor: str | bool | None = None,
        *args: object,
        **kwargs: object,
    ) -> str:
        assert appauthor is False
        return str(tmp_path / "config")

    (tmp_path / "config").mkdir()
    monkeypatch.setattr(paths, "user_data_dir", fake_user_data_dir)
    monkeypatch.setattr(paths, "user_config_dir", fake_user_config_dir)
    monkeypatch.delenv("GOKEEPER_DATA_DIR", raising=False)

    resolved = paths.data_dir()
    assert author_segment not in resolved.parts
    assert resolved == Path(r"C:\Users\test\AppData\Local\gokeeper")


def test_db_path_creates_data_and_backups_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """db_path creates the data dir and backups/ and returns gokeeper.sqlite."""
    data = tmp_path / "data"
    monkeypatch.setenv("GOKEEPER_DATA_DIR", str(data))

    result = paths.db_path()

    assert result == data / "gokeeper.sqlite"
    assert data.is_dir()
    assert (data / "backups").is_dir()


def test_data_dir_falls_through_when_config_lacks_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Config without data_dir falls through to the platform default."""
    config_dir = tmp_path / "config"
    platform_dir = tmp_path / "platform"
    _write_config(config_dir, "# no data_dir key\n")
    _mock_user_config_dir(monkeypatch, config_dir)
    _mock_user_data_dir(monkeypatch, platform_dir)
    monkeypatch.delenv("GOKEEPER_DATA_DIR", raising=False)

    assert paths.data_dir() == platform_dir
