"""Unit tests for matching normalizers (§6.3 / #11)."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from gokeeper.matching.normalizers import (
    default_norm,
    normalize_bool,
    normalize_date,
    normalize_fk,
    normalize_int,
    normalize_level,
    normalize_real,
    normalize_text,
    normalizer_for_kind,
)
from gokeeper.registry import FieldKind


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Hello  ", "hello"),
        ("MiXeD CaSe", "mixed case"),
        ("too   many    spaces", "too many spaces"),
        ("", ""),
        ("   ", ""),
        ("already-clean", "already-clean"),
        (42, "42"),
    ],
)
def test_normalize_text_table(raw: object, expected: str) -> None:
    """Text normalizer strips, casefolds, and collapses internal whitespace."""
    assert normalize_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (True, "1"),
        (False, "0"),
        (1, "1"),
        (0, "0"),
        ("1", "1"),
        ("0", "0"),
        ("true", "1"),
        ("FALSE", "0"),
        ("True", "1"),
    ],
)
def test_normalize_bool_table(raw: object, expected: str) -> None:
    """Bool normalizer maps truthy/falsy forms to \"0\" / \"1\"."""
    assert normalize_bool(raw) == expected


def test_normalize_bool_rejects_unknown_value() -> None:
    """Unrecognized bool inputs raise ValueError."""
    with pytest.raises(ValueError, match="boolean"):
        normalize_bool("maybe")
    with pytest.raises(ValueError, match="boolean"):
        normalize_bool(3.14)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (42, "42"),
        ("42", "42"),
        (0, "0"),
        ("007", "7"),
    ],
)
def test_normalize_int_table(raw: object, expected: str) -> None:
    """INT/FK normalizer emits a decimal integer string."""
    assert normalize_int(raw) == expected
    assert normalize_fk(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (40.5, "40.5"),
        (41.50, "41.5"),
        (40, "40.0"),
        (1.0, "1.0"),
        (51.0, "51.0"),
        ("40.5", "40.5"),
    ],
)
def test_normalize_level_table(raw: object, expected: str) -> None:
    """Level normalizer always formats to one decimal place."""
    assert normalize_level(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (1.25, "1.25"),
        (2.0, "2.0"),
        ("3.5", "3.5"),
    ],
)
def test_normalize_real_table(raw: object, expected: str) -> None:
    """Generic REAL normalizer stringifies the float value."""
    assert normalize_real(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (date(2024, 1, 15), "2024-01-15"),
        (datetime(2024, 1, 15, 13, 45, 0, tzinfo=UTC), "2024-01-15"),
        ("2024-01-15", "2024-01-15"),
        ("2024-01-15T13:45:00", "2024-01-15"),
        ("2024-01-15 13:45:00", "2024-01-15"),
    ],
)
def test_normalize_date_table(raw: object, expected: str) -> None:
    """Date normalizer emits ISO date only, dropping time-of-day."""
    assert normalize_date(raw) == expected


def test_normalize_date_rejects_invalid_string() -> None:
    """Invalid date strings raise ValueError."""
    with pytest.raises(ValueError):
        normalize_date("not-a-date")


def test_normalize_date_rejects_unsupported_type() -> None:
    """Non-date types raise TypeError."""
    with pytest.raises(TypeError, match="cannot normalize date"):
        normalize_date(42)


@pytest.mark.parametrize(
    ("kind", "raw", "expected"),
    [
        (FieldKind.TEXT, "  Hi  ", "hi"),
        (FieldKind.ENUM, "  WILD  ", "wild"),
        (FieldKind.BOOL, True, "1"),
        (FieldKind.INT, 7, "7"),
        (FieldKind.FK, "9", "9"),
        (FieldKind.DATE, date(2020, 5, 1), "2020-05-01"),
        (FieldKind.REAL, 1.5, "1.5"),
    ],
)
def test_normalizer_for_kind_dispatches(
    kind: FieldKind, raw: object, expected: str
) -> None:
    """normalizer_for_kind returns the per-kind normalizer from §6.3."""
    assert normalizer_for_kind(kind)(raw) == expected


def test_default_norm_matches_text_normalizer() -> None:
    """default_norm is the FieldSpec fallback and matches text normalization."""
    assert default_norm("  Hello  ") == normalize_text("  Hello  ")
    assert default_norm is normalize_text
