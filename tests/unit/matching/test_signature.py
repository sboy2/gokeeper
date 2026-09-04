"""Unit tests for signature construction and null policies (§6.2 / #14)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from gokeeper.matching.signature import signature, signature_hash
from gokeeper.models import MatchRule, NullPolicy
from gokeeper.registry import POKEMON_REGISTRY
from gokeeper.registry.core import FieldKind, Registry, build_field_spec

_MATCHING_ROOT = (
    Path(__file__).resolve().parents[3] / "src" / "gokeeper" / "matching"
)

_FORBIDDEN_IMPORT_MODULES = frozenset(
    {
        "sqlite3",
        "pathlib",
        "gokeeper.db",
        "gokeeper.db.connection",
        "gokeeper.db.migrations",
        "gokeeper.db.paths",
    }
)


def _tiny_registry() -> Registry:
    """Minimal registry for focused signature tests."""
    return Registry(
        [
            build_field_spec(
                key="id",
                label="ID",
                kind=FieldKind.INT,
                column="id",
                matchable=False,
            ),
            build_field_spec(
                key="species_id",
                label="Species",
                kind=FieldKind.FK,
                column="species_id",
                fk_table="species",
            ),
            build_field_spec(
                key="is_shiny",
                label="Shiny",
                kind=FieldKind.BOOL,
                column="is_shiny",
            ),
            build_field_spec(
                key="notes",
                label="Notes",
                kind=FieldKind.TEXT,
                column="notes",
                matchable=False,
            ),
        ]
    )


def test_identical_rule_fields_share_signature_despite_notes() -> None:
    """Rows identical on rule fields share a signature even when notes differ."""
    registry = _tiny_registry()
    rule = MatchRule(
        entity_type="pokemon",
        field_keys=("is_shiny", "species_id"),
        null_policy=NullPolicy.NULL_MATCHES_NULL,
    )
    row_a = {"id": 1, "species_id": 25, "is_shiny": True, "notes": "keep"}
    row_b = {"id": 2, "species_id": 25, "is_shiny": True, "notes": "trade"}

    assert signature(rule, row_a, registry) == signature(rule, row_b, registry)


def test_null_never_matches_opts_incomplete_rows_out() -> None:
    """NULL_NEVER_MATCHES returns a per-row unique sentinel for missing fields."""
    registry = _tiny_registry()
    rule = MatchRule(
        entity_type="pokemon",
        field_keys=("is_shiny", "species_id"),
        null_policy=NullPolicy.NULL_NEVER_MATCHES,
    )
    incomplete_a = {"id": 10, "species_id": 1, "is_shiny": None}
    incomplete_b = {"id": 11, "species_id": 1, "is_shiny": None}

    assert signature(rule, incomplete_a, registry) == "__unique__:10"
    assert signature(rule, incomplete_b, registry) == "__unique__:11"
    assert signature(rule, incomplete_a, registry) != signature(
        rule, incomplete_b, registry
    )


def test_null_matches_null_groups_rows_missing_same_field() -> None:
    """NULL_MATCHES_NULL encodes missing values as a shared null sentinel."""
    registry = _tiny_registry()
    rule = MatchRule(
        entity_type="pokemon",
        field_keys=("is_shiny", "species_id"),
        null_policy=NullPolicy.NULL_MATCHES_NULL,
    )
    row_a = {"id": 1, "species_id": 4, "is_shiny": None}
    row_b = {"id": 2, "species_id": 4, "is_shiny": None}

    sig_a = signature(rule, row_a, registry)
    sig_b = signature(rule, row_b, registry)
    assert sig_a == sig_b
    assert "is_shiny=\x00" in sig_a


def test_signature_is_stable_for_fixed_rule_and_row() -> None:
    """A fixed rule and row always produce the same signature string."""
    registry = _tiny_registry()
    rule = MatchRule(
        entity_type="pokemon",
        field_keys=("is_shiny", "species_id"),
        null_policy=NullPolicy.NULL_MATCHES_NULL,
        name="stable",
    )
    row = {"id": 3, "species_id": 7, "is_shiny": False}
    expected = "is_shiny=0|species_id=7"

    assert signature(rule, row, registry) == expected
    assert signature(rule, row, registry) == expected


def test_signature_hash_is_deterministic_blake2b_128() -> None:
    """signature_hash returns a stable 32-char blake2b-128 hex digest."""
    text = "is_shiny=1|species_id=25"
    digest = signature_hash(text)

    assert len(digest) == 32
    assert digest == signature_hash(text)
    assert all(char in "0123456789abcdef" for char in digest)


def test_signature_uses_virtual_compute_on_pokemon_registry() -> None:
    """Virtual fields resolve through compute= on the real Pokémon registry."""
    rule = MatchRule(
        entity_type="pokemon",
        field_keys=("iv_total", "species_id"),
        null_policy=NullPolicy.NULL_MATCHES_NULL,
    )
    row_a = {
        "id": 1,
        "species_id": 4,
        "atk_iv": 15,
        "def_iv": 14,
        "hp_iv": 13,
    }
    row_b = {
        "id": 2,
        "species_id": 4,
        "atk_iv": 15,
        "def_iv": 14,
        "hp_iv": 13,
        "notes": "different",
    }

    assert signature(rule, row_a, POKEMON_REGISTRY) == signature(
        rule, row_b, POKEMON_REGISTRY
    )
    assert signature(rule, row_a, POKEMON_REGISTRY).startswith("iv_total=42|")


@given(
    keys=st.lists(
        st.sampled_from(["is_shiny", "species_id"]),
        min_size=1,
        max_size=2,
        unique=True,
    )
)
def test_sorted_field_keys_produce_identical_signatures(
    keys: list[str],
) -> None:
    """Two rules with the same keys sorted identically share signatures.

    Signature does not re-sort; callers (Block 4) must persist canonical order.
    """
    registry = _tiny_registry()
    row = {"id": 1, "species_id": 99, "is_shiny": True}
    canonical = tuple(sorted(keys))
    rule_a = MatchRule(
        entity_type="pokemon",
        field_keys=canonical,
        null_policy=NullPolicy.NULL_MATCHES_NULL,
    )
    rule_b = MatchRule(
        entity_type="pokemon",
        field_keys=canonical,
        null_policy=NullPolicy.NULL_MATCHES_NULL,
    )
    assert signature(rule_a, row, registry) == signature(rule_b, row, registry)


def test_unsorted_field_keys_change_signature_string() -> None:
    """Different field_keys iteration order yields a different signature string."""
    registry = _tiny_registry()
    row = {"id": 1, "species_id": 99, "is_shiny": True}
    rule_sorted = MatchRule(
        entity_type="pokemon",
        field_keys=("is_shiny", "species_id"),
        null_policy=NullPolicy.NULL_MATCHES_NULL,
    )
    rule_reversed = MatchRule(
        entity_type="pokemon",
        field_keys=("species_id", "is_shiny"),
        null_policy=NullPolicy.NULL_MATCHES_NULL,
    )
    assert signature(rule_sorted, row, registry) != signature(
        rule_reversed, row, registry
    )


def test_matching_package_has_no_io_imports() -> None:
    """matching/ must stay pure — no sqlite3, pathlib, or gokeeper.db imports."""
    py_files = sorted(_MATCHING_ROOT.glob("*.py"))
    assert py_files, f"no Python modules found under {_MATCHING_ROOT}"

    for path in py_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert alias.name not in _FORBIDDEN_IMPORT_MODULES
                    assert root not in {"sqlite3", "pathlib"}
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue
                assert node.module not in _FORBIDDEN_IMPORT_MODULES
                root = node.module.split(".")[0]
                assert root not in {"sqlite3", "pathlib"}
                if node.module == "gokeeper" or node.module.startswith("gokeeper."):
                    assert not node.module.startswith("gokeeper.db")
