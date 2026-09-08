"""Frozen dataclasses for domain values.

Includes in-memory matching types used by the pure signature engine (§6.1–§6.2).
Database-backed models arrive in later blocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class NullPolicy(StrEnum):
    """How missing rule-field values participate in duplicate grouping."""

    NULL_MATCHES_NULL = "NULL_MATCHES_NULL"
    NULL_NEVER_MATCHES = "NULL_NEVER_MATCHES"


@dataclass(frozen=True)
class MatchRule:
    """In-memory duplicate rule (no database identity).

    Parameters
    ----------
    entity_type
        Entity the rule applies to.
    field_keys
        Field registry keys in canonical lexicographic order. Signature
        construction iterates this tuple as-is and does not re-sort.
    null_policy
        Behavior when a rule field is missing on a row.
    name
        Optional display name for presets / debugging.
    """

    entity_type: Literal["pokemon", "postcard"]
    field_keys: tuple[str, ...]
    null_policy: NullPolicy
    name: str = ""
