"""Named match-rule presets (§6.5).

Presets are in-memory field-key sets users can apply as starting rules.
UI guardrails (warnings for ``caught_at``, Whole family, etc.) are Block 6.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from gokeeper.models import MatchRule, NullPolicy
from gokeeper.registry.core import Registry
from gokeeper.registry.pokemon import POKEMON_REGISTRY
from gokeeper.registry.postcard import POSTCARD_REGISTRY

EntityType = Literal["pokemon", "postcard"]


@dataclass(frozen=True)
class MatchPreset:
    """A named, reusable field-key set for duplicate matching.

    Parameters
    ----------
    key
        Stable slug (e.g. ``\"genetic-twin\"``).
    label
        Display name from §6.5.
    entity_type
        Entity the preset applies to.
    field_keys
        Registry keys in lexicographic order (signature does not re-sort).
    """

    key: str
    label: str
    entity_type: EntityType
    field_keys: tuple[str, ...]


def _strict_pokemon_field_keys() -> tuple[str, ...]:
    """Return every matchable Pokémon field key, sorted."""
    return tuple(sorted(spec.key for spec in POKEMON_REGISTRY.matchable_fields()))


ALL_PRESETS: tuple[MatchPreset, ...] = (
    MatchPreset(
        key="genetic-twin",
        label="Genetic twin",
        entity_type="pokemon",
        field_keys=(
            "atk_iv",
            "costume_id",
            "def_iv",
            "form_id",
            "gender",
            "hp_iv",
            "is_shiny",
            "species_id",
        ),
    ),
    MatchPreset(
        key="same-iv-total",
        label="Same IV total",
        entity_type="pokemon",
        field_keys=("form_id", "is_shiny", "iv_total", "species_id"),
    ),
    MatchPreset(
        key="battle-identical",
        label="Battle-identical",
        entity_type="pokemon",
        field_keys=(
            "atk_iv",
            "charged_moveset",
            "def_iv",
            "fast_move_id",
            "form_id",
            "hp_iv",
            "level",
            "species_id",
        ),
    ),
    MatchPreset(
        key="collection-slot",
        label="Collection slot",
        entity_type="pokemon",
        field_keys=(
            "background_id",
            "costume_id",
            "form_id",
            "is_shiny",
            "species_id",
        ),
    ),
    MatchPreset(
        key="family-cluster",
        label="Family cluster",
        entity_type="pokemon",
        field_keys=("costume_id", "family_id", "is_shiny"),
    ),
    MatchPreset(
        key="family-background",
        label="Family + background",
        entity_type="pokemon",
        field_keys=("background_id", "family_id"),
    ),
    MatchPreset(
        key="whole-family",
        label="Whole family",
        entity_type="pokemon",
        field_keys=("family_id",),
    ),
    MatchPreset(
        key="strict",
        label="Strict",
        entity_type="pokemon",
        field_keys=_strict_pokemon_field_keys(),
    ),
    MatchPreset(
        key="same-stop",
        label="Same stop",
        entity_type="postcard",
        field_keys=("pokestop_id",),
    ),
    MatchPreset(
        key="same-stop-sender",
        label="Same stop + sender",
        entity_type="postcard",
        field_keys=("friend_id", "pokestop_id"),
    ),
    MatchPreset(
        key="same-city",
        label="Same city",
        entity_type="postcard",
        field_keys=("city", "country"),
    ),
)


def registry_for(entity_type: EntityType) -> Registry:
    """Return the field registry for an entity type.

    Parameters
    ----------
    entity_type
        ``\"pokemon\"`` or ``\"postcard\"``.

    Returns
    -------
    Registry
        The corresponding module-level registry.
    """
    if entity_type == "pokemon":
        return POKEMON_REGISTRY
    return POSTCARD_REGISTRY


def presets_for(entity_type: EntityType) -> tuple[MatchPreset, ...]:
    """Return presets for one entity type, in declaration order.

    Parameters
    ----------
    entity_type
        ``\"pokemon\"`` or ``\"postcard\"``.

    Returns
    -------
    tuple[MatchPreset, ...]
        Matching presets.
    """
    return tuple(
        preset for preset in ALL_PRESETS if preset.entity_type == entity_type
    )


def get_preset(key: str) -> MatchPreset:
    """Look up a preset by slug.

    Parameters
    ----------
    key
        Preset slug (e.g. ``\"genetic-twin\"``).

    Returns
    -------
    MatchPreset
        Matching preset.

    Raises
    ------
    KeyError
        If no preset has that key.
    """
    for preset in ALL_PRESETS:
        if preset.key == key:
            return preset
    raise KeyError(key)


def validate_preset(preset: MatchPreset, registry: Registry) -> None:
    """Assert every preset key exists and is matchable.

    Parameters
    ----------
    preset
        Preset to validate.
    registry
        Registry for ``preset.entity_type``.

    Raises
    ------
    ValueError
        If a key is missing, not matchable, or ``field_keys`` are unsorted.
    """
    if preset.field_keys != tuple(sorted(preset.field_keys)):
        raise ValueError(
            f"preset {preset.key!r} field_keys are not lexicographically sorted"
        )
    matchable_keys = {spec.key for spec in registry.matchable_fields()}
    for field_key in preset.field_keys:
        if field_key not in registry:
            raise ValueError(
                f"preset {preset.key!r} references unknown field {field_key!r}"
            )
        if field_key not in matchable_keys:
            raise ValueError(
                f"preset {preset.key!r} references non-matchable field {field_key!r}"
            )


def validate_all_presets(
    presets: Iterable[MatchPreset] = ALL_PRESETS,
) -> None:
    """Validate every preset against its entity registry.

    Parameters
    ----------
    presets
        Presets to validate; defaults to ``ALL_PRESETS``.

    Raises
    ------
    ValueError
        If any preset fails ``validate_preset``.
    """
    for preset in presets:
        validate_preset(preset, registry_for(preset.entity_type))


def preset_to_match_rule(
    preset: MatchPreset,
    *,
    null_policy: NullPolicy = NullPolicy.NULL_NEVER_MATCHES,
) -> MatchRule:
    """Convert a preset into an in-memory ``MatchRule``.

    Parameters
    ----------
    preset
        Source preset.
    null_policy
        Null handling for the rule. Defaults to ``NULL_NEVER_MATCHES``, the
        recommended default while inventory rows may be incomplete (§6.2).

    Returns
    -------
    MatchRule
        Rule ready for ``signature()``.
    """
    return MatchRule(
        entity_type=preset.entity_type,
        field_keys=preset.field_keys,
        null_policy=null_policy,
        name=preset.label,
    )
