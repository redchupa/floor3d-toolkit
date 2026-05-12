"""Generate a floor3d-card YAML configuration block."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from floor3d_toolkit.entity_mapper import EntityMapping
from floor3d_toolkit.light_extractor import LightCandidate
from floor3d_toolkit.placement import CameraPlacement, compute_camera

LIGHT_PRESETS: dict[str, dict[str, Any]] = {
    "warm": {
        "lumens": 800,
        "color": "#fff5e0",
        "decay": 1,
        "distance": 450,
        "shadow": "yes",
        "vertical_alignment": "bottom",
    },
    "warm-bright": {
        "lumens": 600,
        "color": "#fff0c8",
        "decay": 1,
        "distance": 450,
        "shadow": "yes",
        "vertical_alignment": "bottom",
    },
    "cool": {
        "lumens": 350,
        "color": "#e8f0ff",
        "decay": 1,
        "distance": 400,
        "shadow": "yes",
        "vertical_alignment": "bottom",
    },
    "daylight": {
        "lumens": 500,
        "color": "#ffffff",
        "decay": 1,
        "distance": 500,
        "shadow": "yes",
        "vertical_alignment": "bottom",
    },
    "subtle": {
        "lumens": 150,
        "color": "#fff4dc",
        "decay": 1,
        "distance": 250,
        "shadow": "no",
        "vertical_alignment": "bottom",
    },
}

DEFAULT_LIGHT_BLOCK: dict[str, Any] = LIGHT_PRESETS["warm"]


# states that mean "active/illuminated" across HA domains.
_ON_LIKE_STATES = (
    "on",
    "playing",
    "open",
    "home",
    "active",
    "running",
    "heating",
    "cooling",
    "drying",
    "washing",
)
# states that should render as "off/dark"
_OFF_LIKE_STATES = (
    "off",
    "idle",
    "paused",
    "standby",
    "closed",
    "away",
    "not_home",
    "unavailable",
    "unknown",
)
_COLOR_ON = "#ffc864"
_COLOR_OFF = "#2d3a55"


def _build_furniture_entry(node: str, entity_id: str) -> dict[str, Any]:
    """Emit a card entity entry whose colorcondition covers the entity's domain.

    ``type3d: color`` crashes floor3d-card if the entity's current state does
    not match any ``colorcondition`` row, so we enumerate the on-like and
    off-like states for the common HA domains.
    """
    domain = entity_id.split(".", 1)[0]
    colorcondition: list[dict[str, str]] = []
    # binary, simple on/off
    if domain in {"light", "switch", "input_boolean", "binary_sensor", "fan"}:
        colorcondition = [
            {"state": "on", "color": _COLOR_ON},
            {"state": "off", "color": _COLOR_OFF},
        ]
    elif domain == "media_player":
        colorcondition = [
            {"state": s, "color": _COLOR_ON} for s in ("playing", "on", "buffering", "paused")
        ] + [
            {"state": s, "color": _COLOR_OFF}
            for s in ("idle", "standby", "off", "unavailable", "unknown")
        ]
    elif domain == "cover":
        colorcondition = [
            {"state": "open", "color": _COLOR_ON},
            {"state": "opening", "color": _COLOR_ON},
            {"state": "closed", "color": _COLOR_OFF},
            {"state": "closing", "color": _COLOR_OFF},
        ]
    else:
        # generic fallback covering both on-like and off-like states
        colorcondition = [
            *[{"state": s, "color": _COLOR_ON} for s in _ON_LIKE_STATES],
            *[{"state": s, "color": _COLOR_OFF} for s in _OFF_LIKE_STATES],
        ]
    return {
        "entity": entity_id,
        "type3d": "color",
        "object_id": node,
        "action": "more-info",
        "colorcondition": colorcondition,
    }


def build_config(
    glb_url: str,
    entity_mappings: list[EntityMapping],
    light_candidates: list[LightCandidate],
    output_path: Path,
    *,
    name: str = "Floor3D",
    style_height_px: int = 600,
    scene_bounds: Any = None,
    camera: CameraPlacement | None = None,
    camera_preset: str = "iso",
    light_preset: str = "warm",
    min_confidence: float = 1.0,
) -> dict[str, Any]:
    """Write a floor3d-card YAML config and return the rendered dict.

    Args:
        glb_url: URL that HA can serve (e.g. ``/local/floor3d/home.glb``).
        entity_mappings: Output of :func:`entity_mapper.suggest_entities`.
        light_candidates: Output of :func:`light_extractor.extract`.
        output_path: Destination YAML path.
        name: Human-readable card title.
        style_height_px: Card height in pixels.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    light_nodes = {c.mesh_node: c for c in light_candidates}
    # Only emit entities where the user explicitly committed (confidence >= 1.0
    # by default). Auto-suggestions stay in entity-mapping.yaml as hints but
    # don't ship to the card — non-existent entity IDs crash floor3d-card on
    # state lookup (e.g. media_player states never match on/off colorcondition).
    mapping_by_node = {
        m.source_name: m
        for m in entity_mappings
        if m.entity_id and m.confidence >= min_confidence
    }

    if light_preset not in LIGHT_PRESETS:
        raise ValueError(
            f"unknown light preset {light_preset!r}; use one of {list(LIGHT_PRESETS)}"
        )
    light_block = LIGHT_PRESETS[light_preset]

    entities: list[dict[str, Any]] = []
    for node, mapping in mapping_by_node.items():
        if node in light_nodes:
            entities.append(
                {
                    "entity": mapping.entity_id,
                    "type3d": "light",
                    "object_id": node,
                    "action": "more-info",
                    "light": dict(light_block),
                }
            )
            continue
        entities.append(_build_furniture_entry(node, mapping.entity_id))

    config: dict[str, Any] = {
        "type": "custom:floor3d-card",
        "name": name,
        "path": "/".join(glb_url.rsplit("/", 1)[:-1]) + "/" if "/" in glb_url else "/local/",
        "objfile": glb_url.rsplit("/", 1)[-1],
        "globalLightPower": 0.45,
        "extralightmode": "yes",
        "shadow": "yes",
        "click": "yes",
        "header": "no",
        "lock_camera": "no",
        "show_axes": "no",
        "sky": "no",
        "style": f"height: {style_height_px}px;",
    }

    if camera is None and scene_bounds is not None:
        camera = compute_camera(scene_bounds, preset=camera_preset)
    if camera is not None:
        config.update(camera.as_card_dict())

    config["entities"] = entities

    output_path.write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return config
