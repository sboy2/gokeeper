"""Unit tests for the postcard field registry (§4.3 / #13)."""

from __future__ import annotations

import pytest

from gokeeper.registry import POSTCARD_REGISTRY
from gokeeper.registry.postcard import (
    DISPOSITION_CHOICES,
    compute_city,
    compute_country,
)

SECTION_4_3_COLUMNS: tuple[str, ...] = (
    "id",
    "friend_id",
    "pokestop_id",
    "opened_at",
    "sticker_id",
    "is_favorite",
    "in_scrapbook",
    "disposition",
    "notes",
    "created_at",
    "updated_at",
)

VIRTUAL_KEYS: tuple[str, ...] = ("city", "country")

PRESET_RELEVANT_KEYS: tuple[str, ...] = (
    "friend_id",
    "pokestop_id",
    "city",
    "country",
)

NON_MATCHABLE_KEYS: frozenset[str] = frozenset(
    {"id", "notes", "created_at", "updated_at"}
)


def test_postcard_registry_covers_section_4_3_columns() -> None:
    """Every §4.3 postcard column has a FieldSpec with a matching column name."""
    for column_name in SECTION_4_3_COLUMNS:
        spec = POSTCARD_REGISTRY[column_name]
        assert spec.column == column_name
        assert spec.compute is None


def test_postcard_registry_keys_are_unique() -> None:
    """Registry keys are exactly §4.3 columns plus virtual location fields."""
    assert len(POSTCARD_REGISTRY.keys()) == len(set(POSTCARD_REGISTRY.keys()))
    assert set(POSTCARD_REGISTRY.keys()) == set(SECTION_4_3_COLUMNS) | set(
        VIRTUAL_KEYS
    )


@pytest.mark.parametrize(
    ("row", "expected_city", "expected_country"),
    [
        (
            {"pokestop_city": "Denver", "pokestop_country": "United States"},
            "Denver",
            "United States",
        ),
        ({"pokestop_city": "Tokyo"}, "Tokyo", None),
        ({}, None, None),
    ],
)
def test_compute_city_and_country_from_joined_row(
    row: dict[str, str],
    expected_city: str | None,
    expected_country: str | None,
) -> None:
    """city/country virtuals read flat pokestop_* join keys from the row."""
    assert compute_city(row) == expected_city
    assert compute_country(row) == expected_country
    assert POSTCARD_REGISTRY["city"].compute is not None
    assert POSTCARD_REGISTRY["country"].compute is not None
    assert POSTCARD_REGISTRY["city"].compute(row) == expected_city
    assert POSTCARD_REGISTRY["country"].compute(row) == expected_country


def test_virtual_fields_have_no_column_and_are_matchable() -> None:
    """Virtual location fields use compute= and remain matchable for presets."""
    for key in VIRTUAL_KEYS:
        spec = POSTCARD_REGISTRY[key]
        assert spec.column is None
        assert spec.compute is not None
        assert spec.matchable is True


def test_preset_relevant_keys_resolve() -> None:
    """§6.5 postcard preset keys all resolve in the registry as matchable."""
    for key in PRESET_RELEVANT_KEYS:
        assert key in POSTCARD_REGISTRY
        assert POSTCARD_REGISTRY[key].matchable is True


def test_matchable_fields_exclude_housekeeping() -> None:
    """Housekeeping fields are excluded from matchable_fields()."""
    matchable_keys = {spec.key for spec in POSTCARD_REGISTRY.matchable_fields()}
    non_matchable_keys = {
        spec.key for spec in POSTCARD_REGISTRY.non_matchable_fields()
    }

    assert NON_MATCHABLE_KEYS <= non_matchable_keys
    assert matchable_keys.isdisjoint(NON_MATCHABLE_KEYS)


def test_disposition_enum_choices() -> None:
    """disposition choices match KEEP/REVIEW/RELEASE."""
    assert POSTCARD_REGISTRY["disposition"].choices == DISPOSITION_CHOICES


def test_postcard_registry_lazy_export_from_package() -> None:
    """POSTCARD_REGISTRY is importable from gokeeper.registry via __getattr__."""
    import gokeeper.registry as registry_package

    assert registry_package.POSTCARD_REGISTRY is POSTCARD_REGISTRY
