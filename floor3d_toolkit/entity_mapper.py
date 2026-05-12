"""Heuristic mapping from Sweet Home 3D names to Home Assistant entity IDs.

Two layers:

1. **Built-in heuristics** — language-agnostic guesses based on the mesh name
   prefix (``light_``, ``furn_``) and a small keyword catalogue. These produce
   *candidate* entity IDs, never authoritative ones.
2. **User overrides** — an optional ``mapping.yaml`` keyed by mesh node name.
   Anything in the override wins.

Per PLAN.md §7, no household-specific vocabulary lives in here. Korean room
labels become ASCII via :mod:`floor3d_toolkit.naming.slugify` before we ever
see them, so the only Korean string this module would ever encounter is one
the user explicitly placed in their own override YAML.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Lightweight keyword catalogue for entity domain guesses. Order = priority.
_DEFAULT_DOMAIN_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("light", "lamp", "downlight", "led", "strip", "mood"), "light"),
    (("switch", "outlet", "plug"), "switch"),
    (("door", "window"), "binary_sensor"),
    (
        ("tv", "monitor", "screen", "computer", "pc", "console"),
        "media_player",
    ),
    (("fan", "purifier", "humidifier", "dehumidifier"), "fan"),
    (("aircon", "ac", "climate", "thermostat", "heater"), "climate"),
    (("vacuum", "robot"), "vacuum"),
)


@dataclass(frozen=True)
class EntityMapping:
    source_name: str
    entity_id: str | None
    confidence: float
    reason: str


@dataclass(frozen=True)
class MappingRules:
    """User-supplied overrides loaded from YAML.

    Values may be ``None`` (explicit opt-out) or a real entity_id string.
    Missing keys fall through to the built-in heuristic.
    """

    by_node: dict[str, str | None] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> MappingRules:
        data: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        by_node = dict(data.get("entities", {}))
        return cls(by_node=by_node)


def _domain_from_keywords(slug: str) -> tuple[str | None, str]:
    # Token-based match, not substring: 'ac' must not match inside 'machine'.
    tokens = set(slug.lower().split("_"))
    for keywords, domain in _DEFAULT_DOMAIN_HINTS:
        for k in keywords:
            if k in tokens:
                return domain, f"keyword '{k}'"
    return None, "no keyword match"


def suggest_entities(
    node_names: list[str],
    rules: MappingRules | None = None,
) -> list[EntityMapping]:
    """Suggest one :class:`EntityMapping` per node name.

    Confidence levels:
    - 1.0  — explicit user override hit
    - 0.6  — keyword hint produced a domain guess
    - 0.0  — no idea, ``entity_id`` is None
    """
    rules = rules or MappingRules()
    out: list[EntityMapping] = []
    for node in node_names:
        if node in rules.by_node:
            override = rules.by_node[node]
            # Explicit null means "user opted out" — keep the entry but skip
            # auto-suggestion so the card omits it entirely.
            if override is None:
                out.append(
                    EntityMapping(
                        source_name=node,
                        entity_id=None,
                        confidence=1.0,
                        reason="user opted out",
                    )
                )
                continue
            out.append(
                EntityMapping(
                    source_name=node,
                    entity_id=override,
                    confidence=1.0,
                    reason="user override",
                )
            )
            continue
        if node.startswith("light_"):
            slug = node[len("light_") :]
            out.append(
                EntityMapping(
                    source_name=node,
                    entity_id=f"light.{slug}",
                    confidence=0.6,
                    reason="light_ prefix",
                )
            )
            continue
        if node.startswith("door_"):
            slug = node[len("door_") :]
            out.append(
                EntityMapping(
                    source_name=node,
                    entity_id=f"binary_sensor.{slug}",
                    confidence=0.4,
                    reason="door_/window_ prefix",
                )
            )
            continue
        if node.startswith("furn_"):
            slug = node[len("furn_") :]
            domain, reason = _domain_from_keywords(slug)
            if domain:
                out.append(
                    EntityMapping(
                        source_name=node,
                        entity_id=f"{domain}.{slug}",
                        confidence=0.6,
                        reason=reason,
                    )
                )
                continue
        out.append(
            EntityMapping(source_name=node, entity_id=None, confidence=0.0, reason="no rule")
        )
    return out


def dump_entity_mapping_yaml(
    mappings: list[EntityMapping],
    output_path: Path,
) -> None:
    """Write a human-editable mapping YAML for users to refine.

    Format::

        # floor3d-toolkit entity mapping
        entities:
          light_living_main: light.living_room_main   # confidence 0.6 (light_ prefix)
          furn_fridge_kitchen: switch.fridge          # confidence 0.6 (keyword 'refrigerator')
          door_main_entry: null                       # confidence 0.0 — fill me in
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        "# floor3d-toolkit entity mapping",
        "# Each key is a mesh node name in your .glb.",
        "# Replace `null` with the matching HA entity_id (light.*, switch.*, etc).",
        "# Heuristic suggestions are shown in comments — they are NOT applied",
        "# until you copy them onto the value side. This protects you from",
        "# accidentally shipping non-existent entity IDs to floor3d-card.",
        "entities:",
    ]
    for m in mappings:
        if m.confidence >= 1.0 and m.entity_id is not None:
            lines.append(
                f"  {m.source_name}: {m.entity_id}  # confidence 1.0 ({m.reason})"
            )
        elif m.entity_id is not None:
            # heuristic suggestion — keep as null so re-runs don't pollute the card
            lines.append(
                f"  {m.source_name}: null  "
                f"# suggested: {m.entity_id}  (confidence {m.confidence:.1f}, {m.reason})"
            )
        else:
            lines.append(
                f"  {m.source_name}: null  # confidence {m.confidence:.1f} ({m.reason})"
            )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
