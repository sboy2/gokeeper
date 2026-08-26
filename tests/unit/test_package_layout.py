"""Smoke tests for the installable package layout (§10)."""


def test_gokeeper_package_imports() -> None:
    """Importing the domain package succeeds."""
    import gokeeper

    assert gokeeper is not None


def test_gokeeper_subpackages_import() -> None:
    """§10 subpackages and models stub are importable."""
    import gokeeper.db
    import gokeeper.matching
    import gokeeper.models
    import gokeeper.registry
    import gokeeper.services

    assert gokeeper.db is not None
    assert gokeeper.services is not None
    assert gokeeper.matching is not None
    assert gokeeper.registry is not None
    assert gokeeper.models is not None


def test_web_package_imports() -> None:
    """Importing the web package succeeds."""
    import web

    assert web is not None
