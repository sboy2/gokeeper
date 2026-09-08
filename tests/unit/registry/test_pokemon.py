"""Unit tests for the Pokémon field registry (§4.1 / #12)."""

from __future__ import annotations

import pytest

from gokeeper.matching.normalizers import normalize_level
from gokeeper.registry import POKEMON_REGISTRY
from gokeeper.registry.pokemon import (
    ORIGIN_CHOICES,
    compute_charged_moveset,
    compute_evolution_stage,
    compute_family_id,
    compute_iv_total,
)

SECTION_4_1_COLUMNS: tuple[str, ...] = (
    "id",
    "species_id",
    "form_id",
    "costume_id",
    "gender",
    "nickname",
    "is_shiny",
    "is_lucky",
    "shadow_state",
    "is_traded",
    "is_favorite",
    "atk_iv",
    "def_iv",
    "hp_iv",
    "cp",
    "hp",
    "level",
    "weight_kg",
    "height_m",
    "size_class",
    "fast_move_id",
    "charged_move_1_id",
    "charged_move_2_id",
    "buddy_level",
    "mega_level",
    "is_dynamax",
    "is_gigantamax",
    "max_attack_level",
    "max_guard_level",
    "max_spirit_level",
    "origin",
    "caught_at",
    "caught_location",
    "background_id",
    "original_trainer",
    "disposition",
    "tags",
    "notes",
    "is_released",
    "released_at",
    "created_at",
    "updated_at",
)

VIRTUAL_KEYS: tuple[str, ...] = (
    "iv_total",
    "charged_moveset",
    "family_id",
    "evolution_stage",
)

NON_MATCHABLE_KEYS: frozenset[str] = frozenset(
    {
        "id",
        "notes",
        "created_at",
        "updated_at",
        "is_released",
        "released_at",
        "tags",
    }
)


def test_pokemon_registry_covers_section_4_1_columns() -> None:
    """Every §4.1 column has a FieldSpec with a matching column name."""
    for column_name in SECTION_4_1_COLUMNS:
        spec = POKEMON_REGISTRY[column_name]
        assert spec.column == column_name
        assert spec.compute is None


def test_pokemon_registry_keys_are_unique() -> None:
    """Registry construction already rejects duplicates; keys match values."""
    assert len(POKEMON_REGISTRY.keys()) == len(set(POKEMON_REGISTRY.keys()))
    assert set(POKEMON_REGISTRY.keys()) == set(SECTION_4_1_COLUMNS) | set(VIRTUAL_KEYS)


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"atk_iv": 15, "def_iv": 14, "hp_iv": 13}, 42),
        ({"atk_iv": 0, "def_iv": 0, "hp_iv": 0}, 0),
        ({"atk_iv": 15, "def_iv": 14}, None),
        ({"atk_iv": None, "def_iv": 14, "hp_iv": 13}, None),
    ],
)
def test_compute_iv_total_table(
    row: dict[str, int | None], expected: int | None
) -> None:
    """iv_total sums IVs and returns None when any component is missing."""
    assert compute_iv_total(row) == expected
    assert POKEMON_REGISTRY["iv_total"].compute is not None
    assert POKEMON_REGISTRY["iv_total"].compute(row) == expected


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        ({"charged_move_1_id": 10, "charged_move_2_id": 20}, "10,20"),
        ({"charged_move_1_id": 20, "charged_move_2_id": 10}, "10,20"),
        ({"charged_move_1_id": 10, "charged_move_2_id": None}, "10"),
        ({"charged_move_1_id": None, "charged_move_2_id": 20}, "20"),
        ({"charged_move_1_id": None, "charged_move_2_id": None}, None),
    ],
)
def test_compute_charged_moveset_table(
    row: dict[str, int | None], expected: str | None
) -> None:
    """charged_moveset is order-invariant and ignores empty slots."""
    assert compute_charged_moveset(row) == expected
    assert POKEMON_REGISTRY["charged_moveset"].compute is not None
    assert POKEMON_REGISTRY["charged_moveset"].compute(row) == expected


def test_charged_moveset_swap_slots_produces_identical_output() -> None:
    """Swapping charged move slots must not change the computed moveset."""
    left = {"charged_move_1_id": 111, "charged_move_2_id": 222}
    right = {"charged_move_1_id": 222, "charged_move_2_id": 111}
    assert compute_charged_moveset(left) == compute_charged_moveset(right)


def test_compute_family_id_and_evolution_stage_from_joined_row() -> None:
    """family_id and evolution_stage read joined values from the row mapping."""
    row = {"family_id": 7, "evolution_stage": 2, "species_id": 4}
    assert compute_family_id(row) == 7
    assert compute_evolution_stage(row) == 2
    assert POKEMON_REGISTRY["family_id"].compute is not None
    assert POKEMON_REGISTRY["evolution_stage"].compute is not None
    assert POKEMON_REGISTRY["family_id"].compute(row) == 7
    assert POKEMON_REGISTRY["evolution_stage"].compute(row) == 2


def test_virtual_fields_have_no_column() -> None:
    """Virtual fields use compute= and leave column unset."""
    for key in VIRTUAL_KEYS:
        spec = POKEMON_REGISTRY[key]
        assert spec.column is None
        assert spec.compute is not None
        assert spec.matchable is True


def test_matchable_fields_exclude_housekeeping() -> None:
    """Housekeeping and id fields are discoverable as non-matchable."""
    matchable_keys = {spec.key for spec in POKEMON_REGISTRY.matchable_fields()}
    non_matchable_keys = {
        spec.key for spec in POKEMON_REGISTRY.non_matchable_fields()
    }

    assert NON_MATCHABLE_KEYS <= non_matchable_keys
    assert matchable_keys.isdisjoint(NON_MATCHABLE_KEYS)
    for key in VIRTUAL_KEYS:
        assert key in matchable_keys


def test_origin_enum_choices_match_architecture() -> None:
    """origin choices match §4.1."""
    assert POKEMON_REGISTRY["origin"].choices == ORIGIN_CHOICES


def test_max_move_levels_are_matchable() -> None:
    """Max Move level columns are eligible for duplicate rules."""
    for key in ("max_attack_level", "max_guard_level", "max_spirit_level"):
        assert POKEMON_REGISTRY[key].matchable is True
        assert POKEMON_REGISTRY[key].kind.value == "INT"


def test_dynamax_and_mega_field_shapes() -> None:
    """Dynamax/Gigantamax are bools; mega_level parallels buddy_level as INT."""
    assert POKEMON_REGISTRY["is_dynamax"].kind.value == "BOOL"
    assert POKEMON_REGISTRY["is_gigantamax"].kind.value == "BOOL"
    assert POKEMON_REGISTRY["mega_level"].kind.value == "INT"
    assert POKEMON_REGISTRY["buddy_level"].kind.value == "INT"
    assert "dynamax_level" not in POKEMON_REGISTRY


def test_level_uses_normalize_level() -> None:
    """level FieldSpec overrides the REAL normalizer with normalize_level."""
    assert POKEMON_REGISTRY["level"].normalizer is normalize_level
    assert POKEMON_REGISTRY["level"].normalizer(40.5) == "40.5"
    assert POKEMON_REGISTRY["level"].normalizer(40.50) == "40.5"


def test_charged_moveset_uses_identity_normalizer() -> None:
    """charged_moveset keeps the compute output without text casefolding."""
    computed = "10,20"
    assert POKEMON_REGISTRY["charged_moveset"].normalizer(computed) == computed


def test_pokemon_registry_lazy_export_from_package() -> None:
    """POKEMON_REGISTRY is importable from gokeeper.registry via __getattr__."""
    import gokeeper.registry as registry_package

    assert registry_package.POKEMON_REGISTRY is POKEMON_REGISTRY


def test_registry_package_unknown_attr_raises() -> None:
    """Unknown attributes on gokeeper.registry raise AttributeError."""
    import gokeeper.registry as registry_package

    with pytest.raises(AttributeError, match="no attribute"):
        _ = registry_package.DOES_NOT_EXIST
