"""Unit tests for match presets (§6.5 / #15)."""

from __future__ import annotations

import pytest

from gokeeper.matching.presets import (
    ALL_PRESETS,
    MatchPreset,
    get_preset,
    preset_to_match_rule,
    presets_for,
    registry_for,
    validate_all_presets,
    validate_preset,
)
from gokeeper.matching.signature import signature, signature_hash
from gokeeper.models import NullPolicy
from gokeeper.registry import POKEMON_REGISTRY, POSTCARD_REGISTRY


@pytest.mark.parametrize("preset", ALL_PRESETS, ids=lambda preset: preset.key)
def test_preset_field_keys_are_sorted_and_matchable(preset: MatchPreset) -> None:
    """Every §6.5 preset has sorted keys that are matchable in its registry."""
    registry = registry_for(preset.entity_type)
    assert preset.field_keys == tuple(sorted(preset.field_keys))
    validate_preset(preset, registry)
    matchable_keys = {spec.key for spec in registry.matchable_fields()}
    assert set(preset.field_keys) <= matchable_keys


def test_validate_all_presets_passes() -> None:
    """ALL_PRESETS validates cleanly against Pokémon and postcard registries."""
    validate_all_presets()


def test_strict_preset_covers_all_matchable_pokemon_fields() -> None:
    """Strict includes every matchable Pokémon field, sorted."""
    strict = get_preset("strict")
    expected = tuple(
        sorted(spec.key for spec in POKEMON_REGISTRY.matchable_fields())
    )
    assert strict.field_keys == expected
    assert strict.entity_type == "pokemon"


def test_presets_for_filters_by_entity_type() -> None:
    """presets_for returns only presets for the requested entity."""
    pokemon_presets = presets_for("pokemon")
    postcard_presets = presets_for("postcard")

    assert pokemon_presets
    assert postcard_presets
    assert all(preset.entity_type == "pokemon" for preset in pokemon_presets)
    assert all(preset.entity_type == "postcard" for preset in postcard_presets)
    assert len(pokemon_presets) + len(postcard_presets) == len(ALL_PRESETS)


def test_registry_for_returns_entity_registries() -> None:
    """registry_for maps entity types to the module-level registries."""
    assert registry_for("pokemon") is POKEMON_REGISTRY
    assert registry_for("postcard") is POSTCARD_REGISTRY


def test_get_preset_and_unknown_key() -> None:
    """get_preset returns known presets and raises KeyError for unknowns."""
    assert get_preset("genetic-twin").label == "Genetic twin"
    with pytest.raises(KeyError):
        get_preset("does-not-exist")


def test_preset_to_match_rule_defaults_null_never_matches() -> None:
    """preset_to_match_rule copies keys/label and defaults null policy."""
    preset = get_preset("same-stop")
    rule = preset_to_match_rule(preset)
    assert rule.entity_type == "postcard"
    assert rule.field_keys == ("pokestop_id",)
    assert rule.null_policy is NullPolicy.NULL_NEVER_MATCHES
    assert rule.name == "Same stop"

    custom = preset_to_match_rule(
        preset, null_policy=NullPolicy.NULL_MATCHES_NULL
    )
    assert custom.null_policy is NullPolicy.NULL_MATCHES_NULL


def test_genetic_twin_signature_spot_check() -> None:
    """Two genetic twins share a signature and hash; a differing IV does not."""
    preset = get_preset("genetic-twin")
    rule = preset_to_match_rule(
        preset, null_policy=NullPolicy.NULL_MATCHES_NULL
    )
    twin_a = {
        "id": 1,
        "species_id": 25,
        "form_id": 1,
        "gender": "FEMALE",
        "is_shiny": True,
        "costume_id": None,
        "atk_iv": 15,
        "def_iv": 14,
        "hp_iv": 13,
        "notes": "a",
    }
    twin_b = {
        **twin_a,
        "id": 2,
        "notes": "b",
    }
    different = {
        **twin_a,
        "id": 3,
        "atk_iv": 10,
    }

    sig_a = signature(rule, twin_a, POKEMON_REGISTRY)
    sig_b = signature(rule, twin_b, POKEMON_REGISTRY)
    sig_diff = signature(rule, different, POKEMON_REGISTRY)

    assert sig_a == sig_b
    assert signature_hash(sig_a) == signature_hash(sig_b)
    assert sig_a != sig_diff


def test_validate_preset_rejects_unknown_field() -> None:
    """validate_preset raises when a key is not in the registry."""
    bad = MatchPreset(
        key="bad",
        label="Bad",
        entity_type="pokemon",
        field_keys=("not_a_real_field",),
    )
    with pytest.raises(ValueError, match="unknown field"):
        validate_preset(bad, POKEMON_REGISTRY)


def test_validate_preset_rejects_non_matchable_field() -> None:
    """validate_preset raises when a key exists but is not matchable."""
    bad = MatchPreset(
        key="bad-notes",
        label="Bad notes",
        entity_type="pokemon",
        field_keys=("notes",),
    )
    with pytest.raises(ValueError, match="non-matchable"):
        validate_preset(bad, POKEMON_REGISTRY)


def test_validate_preset_rejects_unsorted_field_keys() -> None:
    """validate_preset raises when field_keys are not sorted."""
    bad = MatchPreset(
        key="unsorted",
        label="Unsorted",
        entity_type="pokemon",
        field_keys=("species_id", "is_shiny"),
    )
    with pytest.raises(ValueError, match="not lexicographically sorted"):
        validate_preset(bad, POKEMON_REGISTRY)
