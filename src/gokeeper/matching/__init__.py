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
from gokeeper.matching.signature import signature, signature_hash
from gokeeper.models import MatchRule, NullPolicy

__all__ = [
    "MatchRule",
    "NullPolicy",
    "default_norm",
    "normalize_bool",
    "normalize_date",
    "normalize_fk",
    "normalize_int",
    "normalize_level",
    "normalize_real",
    "normalize_text",
    "normalizer_for_kind",
    "signature",
    "signature_hash",
]
