"""Field registry — declarative ``FieldSpec`` definitions per entity type (§2.1)."""

from gokeeper.registry.core import (
    FieldKind,
    FieldSpec,
    Registry,
    build_field_spec,
    default_norm,
    normalizer_for_kind,
)

__all__ = [
    "FieldKind",
    "FieldSpec",
    "Registry",
    "build_field_spec",
    "default_norm",
    "normalizer_for_kind",
]
