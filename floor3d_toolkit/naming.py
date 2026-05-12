"""Stable, ASCII-safe slugs for mesh node names and HA entity hints.

Mesh node names in the .glb are the **only stable handle** floor3d-card uses to
bind to HA entities, so they must be:

1. ASCII (Three.js / glTF accept Unicode but downstream YAML editors choke on Korean)
2. Stable across re-exports — no positional index baked in
3. Collision-free within one scene

This module deliberately avoids any household-specific vocabulary. Korean room
names are romanised via :mod:`unidecode`; collisions are disambiguated with a
numeric suffix only when needed.
"""

from __future__ import annotations

import re

from unidecode import unidecode

_SLUG_INVALID = re.compile(r"[^A-Za-z0-9_]+")
_SLUG_DASH = re.compile(r"_+")


def slugify(value: str, *, max_len: int = 50) -> str:
    """Lowercase ASCII slug suitable for OBJ node names.

    Empty / non-ASCII-recoverable input collapses to ``"item"``.
    """
    if not value:
        return "item"
    ascii_form = unidecode(value).lower()
    cleaned = _SLUG_INVALID.sub("_", ascii_form)
    collapsed = _SLUG_DASH.sub("_", cleaned).strip("_")
    return (collapsed or "item")[:max_len]


class NameAllocator:
    """Hand out unique node names with a stable base.

    The first occurrence of ``base`` returns ``base`` itself; subsequent
    occurrences get ``base_1``, ``base_2``, ... Adding a piece of furniture at
    the end of a Sweet Home 3D session therefore does NOT shift existing names,
    which is critical for floor3d-card entity bindings.
    """

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    def allocate(self, base: str) -> str:
        n = self._counts.get(base, 0)
        self._counts[base] = n + 1
        return base if n == 0 else f"{base}_{n}"
