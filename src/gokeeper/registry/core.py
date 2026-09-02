"""Core field registry types (§2.1).

``FieldSpec`` is the single source of truth for attribute metadata. ``Registry``
collects specs for one entity type and supports keyed lookup and matchable-field
discovery for duplicate rules.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class FieldKind(StrEnum):
    """Supported attribute kinds for ``FieldSpec``."""

    INT = "INT"
    TEXT = "TEXT"
    BOOL = "BOOL"
    ENUM = "ENUM"
    DATE = "DATE"
    REAL = "REAL"
    FK = "FK"


def default_norm(value: Any) -> str:
    """Normalize a field value to its canonical string form.

    Placeholder implementation until ``matching.normalizers`` provides
    per-kind dispatch in #11.

    Parameters
    ----------
    value
        Raw field value from a row mapping.

    Returns
    -------
    str
        String representation of ``value``.
    """
    return str(value)


def normalizer_for_kind(kind: FieldKind) -> Callable[[Any], str]:
    """Return the normalizer for a field kind.

    Stub that delegates to ``default_norm`` for every kind; expanded in #11.

    Parameters
    ----------
    kind
        Attribute kind selecting normalization behavior.

    Returns
    -------
    Callable[[Any], str]
        Normalizer callable for values of ``kind``.
    """
    _ = kind
    return default_norm


@dataclass(frozen=True)
class FieldSpec:
    """Declarative metadata for one tracked attribute.

    Parameters
    ----------
    key
        Stable identifier used in match rules and CSV mapping.
    label
        Human-readable label for forms and tables.
    kind
        Attribute kind controlling widgets, coercion, and default normalization.
    column
        Database column name, or ``None`` for virtual fields.
    compute
        Callable resolving a virtual field from a row mapping.
    fk_table
        Referenced table name when ``kind`` is ``FK``.
    choices
        Allowed enum values when ``kind`` is ``ENUM``.
    normalizer
        Maps a field value to its canonical signature string (§6.3).
    matchable
        Whether the field may appear in duplicate rules.
    csv_aliases
        Alternate CSV header names for import auto-mapping.
    """

    key: str
    label: str
    kind: FieldKind
    column: str | None = None
    compute: Callable[[Mapping[str, Any]], Any] | None = None
    fk_table: str | None = None
    choices: tuple[str, ...] | None = None
    normalizer: Callable[[Any], str] = default_norm
    matchable: bool = True
    csv_aliases: tuple[str, ...] = field(default_factory=tuple)


def build_field_spec(
    key: str,
    label: str,
    kind: FieldKind,
    *,
    column: str | None = None,
    compute: Callable[[Mapping[str, Any]], Any] | None = None,
    fk_table: str | None = None,
    choices: tuple[str, ...] | None = None,
    normalizer: Callable[[Any], str] | None = None,
    matchable: bool = True,
    csv_aliases: tuple[str, ...] = (),
) -> FieldSpec:
    """Construct a ``FieldSpec`` with kind-appropriate defaults.

    Parameters
    ----------
    key
        Stable field identifier.
    label
        Display label.
    kind
        Attribute kind.
    column
        Database column, or ``None`` for virtual fields.
    compute
        Virtual field resolver.
    fk_table
        FK target table when ``kind`` is ``FK``.
    choices
        Enum choices when ``kind`` is ``ENUM``.
    normalizer
        Override normalizer; defaults to ``normalizer_for_kind(kind)``.
    matchable
        Eligible for duplicate rules when ``True``.
    csv_aliases
        CSV header aliases for import.

    Returns
    -------
    FieldSpec
        Frozen field specification.
    """
    resolved_normalizer = normalizer if normalizer is not None else normalizer_for_kind(kind)
    return FieldSpec(
        key=key,
        label=label,
        kind=kind,
        column=column,
        compute=compute,
        fk_table=fk_table,
        choices=choices,
        normalizer=resolved_normalizer,
        matchable=matchable,
        csv_aliases=csv_aliases,
    )


class Registry:
    """Keyed collection of ``FieldSpec`` instances for one entity type.

    Parameters
    ----------
    specs
        Field specifications in definition order.

    Raises
    ------
    ValueError
        If two specs share the same ``key``.
    """

    def __init__(self, specs: Sequence[FieldSpec]) -> None:
        self._specs: tuple[FieldSpec, ...] = tuple(specs)
        self._by_key: dict[str, FieldSpec] = {}
        for spec in self._specs:
            if spec.key in self._by_key:
                raise ValueError(f"duplicate field key: {spec.key!r}")
            self._by_key[spec.key] = spec

    def __getitem__(self, key: str) -> FieldSpec:
        """Return the spec for ``key``.

        Raises
        ------
        KeyError
            If ``key`` is not registered.
        """
        return self._by_key[key]

    def __iter__(self) -> Iterator[FieldSpec]:
        """Iterate specs in definition order."""
        return iter(self._specs)

    def __len__(self) -> int:
        """Return the number of registered fields."""
        return len(self._specs)

    def __contains__(self, key: object) -> bool:
        """Return whether ``key`` is a registered field key."""
        return isinstance(key, str) and key in self._by_key

    def keys(self) -> tuple[str, ...]:
        """Return field keys in definition order."""
        return tuple(spec.key for spec in self._specs)

    def values(self) -> tuple[FieldSpec, ...]:
        """Return specs in definition order."""
        return self._specs

    def matchable_fields(self) -> tuple[FieldSpec, ...]:
        """Return specs eligible for duplicate rules, in definition order."""
        return tuple(spec for spec in self._specs if spec.matchable)

    def non_matchable_fields(self) -> tuple[FieldSpec, ...]:
        """Return specs excluded from duplicate rules, in definition order."""
        return tuple(spec for spec in self._specs if not spec.matchable)
