"""Pure signature construction for duplicate matching (§6.1–§6.2).

Takes a rule, a row mapping, and a field registry — no database or I/O.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from gokeeper.models import MatchRule, NullPolicy
from gokeeper.registry.core import Registry

_NULL_SENTINEL = "\x00"


def signature(
    rule: MatchRule, row: Mapping[str, Any], registry: Registry
) -> str:
    """Build the canonical readable signature string for a row under a rule.

    Parameters
    ----------
    rule
        Match rule whose ``field_keys`` are already lexicographically sorted.
    row
        Attribute mapping for one entity instance. Must include ``id`` when
        ``null_policy`` is ``NULL_NEVER_MATCHES``.
    registry
        Field registry for ``rule.entity_type``.

    Returns
    -------
    str
        Pipe-joined ``key=normalized`` parts, or ``__unique__:{id}`` when
        ``NULL_NEVER_MATCHES`` encounters a missing rule field.
    """
    parts: list[str] = []
    for key in rule.field_keys:
        spec = registry[key]
        value = spec.compute(row) if spec.compute is not None else row.get(key)
        if value is None:
            if rule.null_policy is NullPolicy.NULL_NEVER_MATCHES:
                return f"__unique__:{row['id']}"
            parts.append(f"{key}={_NULL_SENTINEL}")
        else:
            parts.append(f"{key}={spec.normalizer(value)}")
    return "|".join(parts)


def signature_hash(signature_text: str) -> str:
    """Return the blake2b-128 hex digest of a signature string (§6.1).

    Parameters
    ----------
    signature_text
        Readable signature from ``signature()``.

    Returns
    -------
    str
        32-character lowercase hex digest.
    """
    digest = hashlib.blake2b(signature_text.encode(), digest_size=16)
    return digest.hexdigest()
