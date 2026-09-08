"""Field registry — declarative ``FieldSpec`` definitions per entity type (§2.1)."""

from typing import Any

from gokeeper.registry.core import (
    FieldKind,
    FieldSpec,
    Registry,
    build_field_spec,
    default_norm,
    normalizer_for_kind,
)

__all__ = [
    "POKEMON_REGISTRY",
    "POSTCARD_REGISTRY",
    "FieldKind",
    "FieldSpec",
    "Registry",
    "build_field_spec",
    "default_norm",
    "normalizer_for_kind",
]


def __getattr__(name: str) -> Any:
    """Lazy-load entity registries to avoid matching ↔ registry import cycles."""
    if name == "POKEMON_REGISTRY":
        from gokeeper.registry.pokemon import POKEMON_REGISTRY

        return POKEMON_REGISTRY
    if name == "POSTCARD_REGISTRY":
        from gokeeper.registry.postcard import POSTCARD_REGISTRY

        return POSTCARD_REGISTRY
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
