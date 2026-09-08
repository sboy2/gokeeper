"""Pokémon field registry (§4.1, §6.3).

Declares one ``FieldSpec`` per Pokémon attribute plus virtual match fields
(``iv_total``, ``charged_moveset``, ``family_id``, ``evolution_stage``).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from gokeeper.matching.normalizers import normalize_level
from gokeeper.registry.core import FieldKind, Registry, build_field_spec

ORIGIN_CHOICES: tuple[str, ...] = (
    "WILD",
    "RAID",
    "EGG",
    "RESEARCH",
    "TRADE",
    "BATTLE_LEAGUE",
    "INCENSE",
    "PURIFY",
    "EVOLVE",
    "MAX_BATTLE",
    "OTHER",
)

SHADOW_STATE_CHOICES: tuple[str, ...] = ("NORMAL", "SHADOW", "PURIFIED")

DISPOSITION_CHOICES: tuple[str, ...] = ("KEEP", "REVIEW", "RELEASE")

GENDER_CHOICES: tuple[str, ...] = ("MALE", "FEMALE", "GENDERLESS")


def compute_iv_total(row: Mapping[str, Any]) -> int | None:
    """Sum Attack, Defense, and HP IVs from a row mapping.

    Parameters
    ----------
    row
        Pokémon attribute mapping. Missing any IV yields ``None`` so signature
        null policies can apply.

    Returns
    -------
    int | None
        IV total, or ``None`` if any component is missing.
    """
    atk_iv = row.get("atk_iv")
    def_iv = row.get("def_iv")
    hp_iv = row.get("hp_iv")
    if atk_iv is None or def_iv is None or hp_iv is None:
        return None
    return int(atk_iv) + int(def_iv) + int(hp_iv)


def compute_charged_moveset(row: Mapping[str, Any]) -> str | None:
    """Build an order-invariant charged-move signature fragment.

    Sorts the two charged move IDs so slot order does not affect matching.
    ``None`` slots are ignored; both missing yields ``None``.

    Parameters
    ----------
    row
        Pokémon attribute mapping with ``charged_move_1_id`` /
        ``charged_move_2_id``.

    Returns
    -------
    str | None
        Comma-joined sorted move IDs, or ``None`` when both slots are empty.
    """
    move_1 = row.get("charged_move_1_id")
    move_2 = row.get("charged_move_2_id")
    if move_1 is None and move_2 is None:
        return None
    move_ids = sorted(int(move_id) for move_id in (move_1, move_2) if move_id is not None)
    return ",".join(str(move_id) for move_id in move_ids)


def compute_family_id(row: Mapping[str, Any]) -> Any:
    """Read joined ``family_id`` supplied by the caller on the row mapping.

    Parameters
    ----------
    row
        Mapping that includes species-joined ``family_id`` when available.

    Returns
    -------
    Any
        Family id, or ``None`` if absent.
    """
    return row.get("family_id")


def compute_evolution_stage(row: Mapping[str, Any]) -> Any:
    """Read joined ``evolution_stage`` supplied by the caller on the row mapping.

    Parameters
    ----------
    row
        Mapping that includes species-joined ``evolution_stage`` when available.

    Returns
    -------
    Any
        Evolution stage, or ``None`` if absent.
    """
    return row.get("evolution_stage")


def _identity_normalizer(value: Any) -> str:
    """Pass through an already-canonical computed string."""
    return str(value)


POKEMON_REGISTRY = Registry(
    [
        # Identity
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
            csv_aliases=("Species", "Pokemon", "Pokémon"),
        ),
        build_field_spec(
            key="form_id",
            label="Form",
            kind=FieldKind.FK,
            column="form_id",
            fk_table="form",
            csv_aliases=("Form",),
        ),
        build_field_spec(
            key="costume_id",
            label="Costume",
            kind=FieldKind.FK,
            column="costume_id",
            fk_table="costume",
            csv_aliases=("Costume",),
        ),
        build_field_spec(
            key="gender",
            label="Gender",
            kind=FieldKind.ENUM,
            column="gender",
            choices=GENDER_CHOICES,
            csv_aliases=("Gender",),
        ),
        build_field_spec(
            key="nickname",
            label="Nickname",
            kind=FieldKind.TEXT,
            column="nickname",
            csv_aliases=("Nickname", "Name"),
        ),
        # Rarity flags
        build_field_spec(
            key="is_shiny",
            label="Shiny",
            kind=FieldKind.BOOL,
            column="is_shiny",
            csv_aliases=("Shiny", "Is Shiny"),
        ),
        build_field_spec(
            key="is_lucky",
            label="Lucky",
            kind=FieldKind.BOOL,
            column="is_lucky",
            csv_aliases=("Lucky", "Is Lucky"),
        ),
        build_field_spec(
            key="shadow_state",
            label="Shadow state",
            kind=FieldKind.ENUM,
            column="shadow_state",
            choices=SHADOW_STATE_CHOICES,
            csv_aliases=("Shadow", "Shadow State"),
        ),
        build_field_spec(
            key="is_traded",
            label="Traded",
            kind=FieldKind.BOOL,
            column="is_traded",
            csv_aliases=("Traded", "Is Traded"),
        ),
        build_field_spec(
            key="is_favorite",
            label="Favorite",
            kind=FieldKind.BOOL,
            column="is_favorite",
            csv_aliases=("Favorite", "Favourite"),
        ),
        # Stats
        build_field_spec(
            key="atk_iv",
            label="Attack IV",
            kind=FieldKind.INT,
            column="atk_iv",
            csv_aliases=("Attack IV", "Atk IV", "ATK"),
        ),
        build_field_spec(
            key="def_iv",
            label="Defense IV",
            kind=FieldKind.INT,
            column="def_iv",
            csv_aliases=("Defense IV", "Def IV", "DEF"),
        ),
        build_field_spec(
            key="hp_iv",
            label="HP IV",
            kind=FieldKind.INT,
            column="hp_iv",
            csv_aliases=("HP IV", "Stamina IV", "STA"),
        ),
        build_field_spec(
            key="cp",
            label="CP",
            kind=FieldKind.INT,
            column="cp",
            csv_aliases=("CP",),
        ),
        build_field_spec(
            key="hp",
            label="HP",
            kind=FieldKind.INT,
            column="hp",
            csv_aliases=("HP",),
        ),
        build_field_spec(
            key="level",
            label="Level",
            kind=FieldKind.REAL,
            column="level",
            normalizer=normalize_level,
            csv_aliases=("Level", "Lvl"),
        ),
        build_field_spec(
            key="weight_kg",
            label="Weight (kg)",
            kind=FieldKind.REAL,
            column="weight_kg",
            csv_aliases=("Weight", "Weight kg"),
        ),
        build_field_spec(
            key="height_m",
            label="Height (m)",
            kind=FieldKind.REAL,
            column="height_m",
            csv_aliases=("Height", "Height m"),
        ),
        build_field_spec(
            key="size_class",
            label="Size class",
            kind=FieldKind.TEXT,
            column="size_class",
            csv_aliases=("Size", "Size Class"),
        ),
        # Moves
        build_field_spec(
            key="fast_move_id",
            label="Fast move",
            kind=FieldKind.FK,
            column="fast_move_id",
            fk_table="move",
            csv_aliases=("Fast Move", "Quick Move"),
        ),
        build_field_spec(
            key="charged_move_1_id",
            label="Charged move 1",
            kind=FieldKind.FK,
            column="charged_move_1_id",
            fk_table="move",
            csv_aliases=("Charged Move 1", "Charge Move 1"),
        ),
        build_field_spec(
            key="charged_move_2_id",
            label="Charged move 2",
            kind=FieldKind.FK,
            column="charged_move_2_id",
            fk_table="move",
            csv_aliases=("Charged Move 2", "Charge Move 2"),
        ),
        # Buddy / Mega / Max
        build_field_spec(
            key="buddy_level",
            label="Buddy level",
            kind=FieldKind.INT,
            column="buddy_level",
            csv_aliases=("Buddy Level",),
        ),
        build_field_spec(
            key="mega_level",
            label="Mega level",
            kind=FieldKind.INT,
            column="mega_level",
            csv_aliases=("Mega Level", "Mega"),
        ),
        build_field_spec(
            key="is_dynamax",
            label="Dynamax",
            kind=FieldKind.BOOL,
            column="is_dynamax",
            csv_aliases=("Dynamax", "Is Dynamax"),
        ),
        build_field_spec(
            key="is_gigantamax",
            label="Gigantamax",
            kind=FieldKind.BOOL,
            column="is_gigantamax",
            csv_aliases=("Gigantamax", "Is Gigantamax"),
        ),
        build_field_spec(
            key="max_attack_level",
            label="Max Attack level",
            kind=FieldKind.INT,
            column="max_attack_level",
            csv_aliases=("Max Attack Level", "Max Attack"),
        ),
        build_field_spec(
            key="max_guard_level",
            label="Max Guard level",
            kind=FieldKind.INT,
            column="max_guard_level",
            csv_aliases=("Max Guard Level", "Max Guard"),
        ),
        build_field_spec(
            key="max_spirit_level",
            label="Max Spirit level",
            kind=FieldKind.INT,
            column="max_spirit_level",
            csv_aliases=("Max Spirit Level", "Max Spirit"),
        ),
        # Provenance
        build_field_spec(
            key="origin",
            label="Origin",
            kind=FieldKind.ENUM,
            column="origin",
            choices=ORIGIN_CHOICES,
            csv_aliases=("Origin", "Caught From"),
        ),
        build_field_spec(
            key="caught_at",
            label="Caught at",
            kind=FieldKind.DATE,
            column="caught_at",
            csv_aliases=("Caught At", "Catch Date", "Date Caught"),
        ),
        build_field_spec(
            key="caught_location",
            label="Caught location",
            kind=FieldKind.TEXT,
            column="caught_location",
            csv_aliases=("Caught Location", "Location"),
        ),
        build_field_spec(
            key="background_id",
            label="Background",
            kind=FieldKind.FK,
            column="background_id",
            fk_table="background",
            csv_aliases=("Background",),
        ),
        build_field_spec(
            key="original_trainer",
            label="Original trainer",
            kind=FieldKind.TEXT,
            column="original_trainer",
            csv_aliases=("OT", "Original Trainer"),
        ),
        # Workflow
        build_field_spec(
            key="disposition",
            label="Disposition",
            kind=FieldKind.ENUM,
            column="disposition",
            choices=DISPOSITION_CHOICES,
            csv_aliases=("Disposition",),
        ),
        # Housekeeping
        build_field_spec(
            key="tags",
            label="Tags",
            kind=FieldKind.TEXT,
            column="tags",
            matchable=False,
        ),
        build_field_spec(
            key="notes",
            label="Notes",
            kind=FieldKind.TEXT,
            column="notes",
            matchable=False,
            csv_aliases=("Notes",),
        ),
        build_field_spec(
            key="is_released",
            label="Released",
            kind=FieldKind.BOOL,
            column="is_released",
            matchable=False,
        ),
        build_field_spec(
            key="released_at",
            label="Released at",
            kind=FieldKind.DATE,
            column="released_at",
            matchable=False,
        ),
        build_field_spec(
            key="created_at",
            label="Created at",
            kind=FieldKind.DATE,
            column="created_at",
            matchable=False,
        ),
        build_field_spec(
            key="updated_at",
            label="Updated at",
            kind=FieldKind.DATE,
            column="updated_at",
            matchable=False,
        ),
        # Virtual fields (§6.3)
        build_field_spec(
            key="iv_total",
            label="IV total",
            kind=FieldKind.INT,
            column=None,
            compute=compute_iv_total,
            csv_aliases=("IV Total", "Total IV"),
        ),
        build_field_spec(
            key="charged_moveset",
            label="Charged moveset",
            kind=FieldKind.TEXT,
            column=None,
            compute=compute_charged_moveset,
            normalizer=_identity_normalizer,
        ),
        build_field_spec(
            key="family_id",
            label="Evolution family",
            kind=FieldKind.FK,
            column=None,
            compute=compute_family_id,
            fk_table="evolution_family",
        ),
        build_field_spec(
            key="evolution_stage",
            label="Evolution stage",
            kind=FieldKind.INT,
            column=None,
            compute=compute_evolution_stage,
        ),
    ]
)
