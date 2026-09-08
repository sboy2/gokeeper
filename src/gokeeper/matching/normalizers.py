"""Field-value normalizers for duplicate signatures (§6.3).

Normalizers map raw row values to canonical strings used in ``signature()``.
They are pure: no database or filesystem access.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime
from typing import Any

from gokeeper.registry.core import FieldKind


def normalize_text(value: Any) -> str:
    """Normalize text for matching: strip, casefold, collapse whitespace.

    Parameters
    ----------
    value
        Raw field value. Non-strings are converted with ``str`` first.

    Returns
    -------
    str
        Canonical text form.
    """
    text = str(value).strip().casefold()
    return " ".join(text.split())


def normalize_bool(value: Any) -> str:
    """Normalize a boolean-like value to ``\"0\"`` or ``\"1\"``.

    Parameters
    ----------
    value
        ``bool``, ``0``/``1``, or strings ``\"0\"``/``\"1\"``/``\"true\"``/``\"false\"``
        (case-insensitive).

    Returns
    -------
    str
        ``\"1\"`` for true, ``\"0\"`` for false.

    Raises
    ------
    ValueError
        If ``value`` cannot be interpreted as a boolean.
    """
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int) and value in (0, 1):
        return str(value)
    if isinstance(value, str):
        folded = value.strip().casefold()
        if folded in {"1", "true"}:
            return "1"
        if folded in {"0", "false"}:
            return "0"
    raise ValueError(f"cannot normalize boolean value: {value!r}")


def normalize_int(value: Any) -> str:
    """Normalize an integer or FK id to a decimal string.

    Parameters
    ----------
    value
        Integer or string form of an integer (display names are never passed).

    Returns
    -------
    str
        Canonical integer string (e.g. ``\"42\"``).
    """
    return str(int(value))


normalize_fk = normalize_int


def normalize_level(value: Any) -> str:
    """Normalize a Pokémon level to one decimal place.

    Half-step levels (e.g. ``40.5``) must compare equal regardless of input
    formatting such as ``40.50``.

    Parameters
    ----------
    value
        Numeric level or string parseable as float.

    Returns
    -------
    str
        Level formatted with ``f\"{value:.1f}\"``.
    """
    return f"{float(value):.1f}"


def normalize_real(value: Any) -> str:
    """Normalize a generic REAL value for matching.

    Field-specific overrides (notably ``level`` → ``normalize_level``) should
    be set on the corresponding ``FieldSpec``.

    Parameters
    ----------
    value
        Numeric value or string parseable as float.

    Returns
    -------
    str
        ``str(float(value))`` form.
    """
    return str(float(value))


def normalize_date(value: Any) -> str:
    """Normalize a date to ISO ``YYYY-MM-DD`` (no time-of-day).

    Parameters
    ----------
    value
        ``date``, ``datetime``, or ISO date/datetime string.

    Returns
    -------
    str
        ISO date string.

    Raises
    ------
    ValueError
        If ``value`` cannot be parsed as a date.
    TypeError
        If ``value`` is an unsupported type.
    """
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        text = value.strip()
        if "T" in text:
            return datetime.fromisoformat(text).date().isoformat()
        if " " in text:
            return datetime.fromisoformat(text).date().isoformat()
        return date.fromisoformat(text).isoformat()
    raise TypeError(f"cannot normalize date value of type {type(value).__name__}")


default_norm = normalize_text


def normalizer_for_kind(kind: FieldKind) -> Callable[[Any], str]:
    """Return the default normalizer for a ``FieldKind``.

    ``level`` and other field-specific overrides are applied on the
    ``FieldSpec``, not here. ``ENUM`` uses text normalization; ``REAL`` uses
    the generic real normalizer.

    Parameters
    ----------
    kind
        Attribute kind selecting normalization behavior.

    Returns
    -------
    Callable[[Any], str]
        Normalizer for values of ``kind``.
    """
    mapping: dict[FieldKind, Callable[[Any], str]] = {
        FieldKind.TEXT: normalize_text,
        FieldKind.ENUM: normalize_text,
        FieldKind.BOOL: normalize_bool,
        FieldKind.INT: normalize_int,
        FieldKind.FK: normalize_fk,
        FieldKind.DATE: normalize_date,
        FieldKind.REAL: normalize_real,
    }
    return mapping[kind]
