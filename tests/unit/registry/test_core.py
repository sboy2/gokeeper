"""Unit tests for the field registry core types (§2.1 / #10)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from gokeeper.registry import FieldKind, FieldSpec, Registry


def _identity_normalizer(value: Any) -> str:
    """Test normalizer that stringifies values."""
    return str(value)


def test_registry_lookup_by_key() -> None:
    """A registry built from specs supports keyed lookup."""
    species = FieldSpec(
        key="species_id",
        label="Species",
        kind=FieldKind.FK,
        column="species_id",
        fk_table="species",
        normalizer=_identity_normalizer,
    )
    nickname = FieldSpec(
        key="nickname",
        label="Nickname",
        kind=FieldKind.TEXT,
        column="nickname",
        normalizer=_identity_normalizer,
    )
    registry = Registry([species, nickname])

    assert registry["species_id"] is species
    assert registry["nickname"] is nickname


def test_registry_duplicate_key_raises() -> None:
    """Duplicate field keys are rejected at construction time."""
    duplicate = FieldSpec(
        key="species_id",
        label="Species",
        kind=FieldKind.FK,
        normalizer=_identity_normalizer,
    )
    with pytest.raises(ValueError, match="duplicate field key"):
        Registry([duplicate, duplicate])


def test_registry_matchable_fields_excludes_non_matchable() -> None:
    """matchable_fields returns only specs with matchable=True in definition order."""
    matchable = FieldSpec(
        key="species_id",
        label="Species",
        kind=FieldKind.FK,
        normalizer=_identity_normalizer,
        matchable=True,
    )
    notes = FieldSpec(
        key="notes",
        label="Notes",
        kind=FieldKind.TEXT,
        normalizer=_identity_normalizer,
        matchable=False,
    )
    registry = Registry([matchable, notes])

    assert registry.matchable_fields() == (matchable,)
    assert registry.non_matchable_fields() == (notes,)


def test_registry_virtual_field_has_compute_and_no_column() -> None:
    """Virtual fields use compute instead of a database column."""

    def compute_iv_total(row: Mapping[str, Any]) -> int:
        return row["atk_iv"] + row["def_iv"] + row["hp_iv"]

    iv_total = FieldSpec(
        key="iv_total",
        label="IV total",
        kind=FieldKind.INT,
        column=None,
        compute=compute_iv_total,
        normalizer=_identity_normalizer,
    )
    registry = Registry([iv_total])

    assert iv_total.column is None
    assert iv_total.compute is not None
    assert iv_total.compute({"atk_iv": 15, "def_iv": 14, "hp_iv": 13}) == 42
    assert registry["iv_total"] is iv_total


def test_registry_iterate_keys_and_values() -> None:
    """Registry supports iteration and keys/values views."""
    first = FieldSpec(
        key="a",
        label="A",
        kind=FieldKind.TEXT,
        normalizer=_identity_normalizer,
    )
    second = FieldSpec(
        key="b",
        label="B",
        kind=FieldKind.TEXT,
        normalizer=_identity_normalizer,
    )
    registry = Registry([first, second])

    assert list(registry) == [first, second]
    assert list(registry.keys()) == ["a", "b"]
    assert list(registry.values()) == [first, second]
    assert len(registry) == 2
    assert "a" in registry
    assert "missing" not in registry


def test_registry_missing_key_raises_key_error() -> None:
    """Lookup of an unknown key raises KeyError."""
    registry = Registry(
        [
            FieldSpec(
                key="only",
                label="Only",
                kind=FieldKind.TEXT,
                normalizer=_identity_normalizer,
            )
        ]
    )

    with pytest.raises(KeyError):
        _ = registry["missing"]


def test_field_kind_covers_all_kinds() -> None:
    """FieldKind enumerates every supported attribute kind from §2.1."""
    assert set(FieldKind) == {
        FieldKind.INT,
        FieldKind.TEXT,
        FieldKind.BOOL,
        FieldKind.ENUM,
        FieldKind.DATE,
        FieldKind.REAL,
        FieldKind.FK,
    }


def test_default_norm_stringifies_value() -> None:
    """default_norm is a placeholder normalizer until #11 wires per-kind dispatch."""
    from gokeeper.registry.core import default_norm

    assert default_norm(42) == "42"
    assert default_norm("hello") == "hello"


def test_normalizer_for_kind_returns_callable() -> None:
    """normalizer_for_kind returns a callable (stub expanded in #11)."""
    from gokeeper.registry.core import default_norm, normalizer_for_kind

    normalizer = normalizer_for_kind(FieldKind.TEXT)
    assert callable(normalizer)
    assert normalizer("x") == default_norm("x")


def test_field_spec_uses_default_normalizer() -> None:
    """FieldSpec defaults normalizer to default_norm when not provided."""
    from gokeeper.registry.core import default_norm

    spec = FieldSpec(key="x", label="X", kind=FieldKind.TEXT)
    assert spec.normalizer is default_norm


def test_build_field_spec_assigns_kind_normalizer() -> None:
    """build_field_spec wires normalizer_for_kind when normalizer is omitted."""
    from gokeeper.registry.core import build_field_spec, normalizer_for_kind

    spec = build_field_spec(key="level", label="Level", kind=FieldKind.REAL)
    assert spec.normalizer is normalizer_for_kind(FieldKind.REAL)
