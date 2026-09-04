"""Postcard field registry (§4.3, §6.5).

Declares one ``FieldSpec`` per postcard attribute plus virtual pokestop
location fields (``city``, ``country``) for match presets.

Joined pokestop values are expected on the row as flat prefixed keys
(``pokestop_city``, ``pokestop_country``); services populate them later.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from gokeeper.registry.core import FieldKind, Registry, build_field_spec

DISPOSITION_CHOICES: tuple[str, ...] = ("KEEP", "REVIEW", "RELEASE")


def compute_city(row: Mapping[str, Any]) -> Any:
    """Read joined pokestop city from a flat row mapping.

    Parameters
    ----------
    row
        Postcard row with optional ``pokestop_city`` from a pokestop join.

    Returns
    -------
    Any
        City string, or ``None`` if absent.
    """
    return row.get("pokestop_city")


def compute_country(row: Mapping[str, Any]) -> Any:
    """Read joined pokestop country from a flat row mapping.

    Parameters
    ----------
    row
        Postcard row with optional ``pokestop_country`` from a pokestop join.

    Returns
    -------
    Any
        Country string, or ``None`` if absent.
    """
    return row.get("pokestop_country")


POSTCARD_REGISTRY = Registry(
    [
        build_field_spec(
            key="id",
            label="ID",
            kind=FieldKind.INT,
            column="id",
            matchable=False,
        ),
        build_field_spec(
            key="friend_id",
            label="Friend",
            kind=FieldKind.FK,
            column="friend_id",
            fk_table="friend",
            csv_aliases=("Friend", "Sender"),
        ),
        build_field_spec(
            key="pokestop_id",
            label="PokéStop",
            kind=FieldKind.FK,
            column="pokestop_id",
            fk_table="pokestop",
            csv_aliases=("PokéStop", "Pokestop", "Stop"),
        ),
        build_field_spec(
            key="opened_at",
            label="Opened at",
            kind=FieldKind.DATE,
            column="opened_at",
            csv_aliases=("Opened At", "Open Date", "Date Opened"),
        ),
        build_field_spec(
            key="sticker_id",
            label="Sticker",
            kind=FieldKind.FK,
            column="sticker_id",
            fk_table="sticker",
            csv_aliases=("Sticker",),
        ),
        build_field_spec(
            key="is_favorite",
            label="Favorite",
            kind=FieldKind.BOOL,
            column="is_favorite",
            csv_aliases=("Favorite", "Favourite"),
        ),
        build_field_spec(
            key="in_scrapbook",
            label="In scrapbook",
            kind=FieldKind.BOOL,
            column="in_scrapbook",
            csv_aliases=("Scrapbook", "In Scrapbook"),
        ),
        build_field_spec(
            key="disposition",
            label="Disposition",
            kind=FieldKind.ENUM,
            column="disposition",
            choices=DISPOSITION_CHOICES,
            csv_aliases=("Disposition",),
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
        # Virtual joined fields for §6.5 presets (Same city)
        build_field_spec(
            key="city",
            label="City",
            kind=FieldKind.TEXT,
            column=None,
            compute=compute_city,
            csv_aliases=("City",),
        ),
        build_field_spec(
            key="country",
            label="Country",
            kind=FieldKind.TEXT,
            column=None,
            compute=compute_country,
            csv_aliases=("Country",),
        ),
    ]
)
