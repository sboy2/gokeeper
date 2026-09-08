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
from gokeeper.matching.presets import (
    ALL_PRESETS,
    MatchPreset,
    get_preset,
    preset_to_match_rule,
    presets_for,
    registry_for,
    validate_all_presets,
    validate_preset,
)
from gokeeper.matching.signature import signature, signature_hash
from gokeeper.models import MatchRule, NullPolicy

__all__ = [
    "ALL_PRESETS",
    "MatchPreset",
    "MatchRule",
    "NullPolicy",
    "default_norm",
    "get_preset",
    "normalize_bool",
    "normalize_date",
    "normalize_fk",
    "normalize_int",
    "normalize_level",
    "normalize_real",
    "normalize_text",
    "normalizer_for_kind",
    "preset_to_match_rule",
    "presets_for",
    "registry_for",
    "signature",
    "signature_hash",
    "validate_all_presets",
    "validate_preset",
]
