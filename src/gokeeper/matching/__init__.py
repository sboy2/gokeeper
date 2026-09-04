"""Pure matching engine — normalizers, signatures, and presets (§6)."""

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

__all__ = [
    "default_norm",
    "normalize_bool",
    "normalize_date",
    "normalize_fk",
    "normalize_int",
    "normalize_level",
    "normalize_real",
    "normalize_text",
    "normalizer_for_kind",
]
