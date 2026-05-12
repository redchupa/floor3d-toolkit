"""Compute sensible camera positions from a scene's bounding box.

floor3d-card uses Three.js conventions:
    +x right, +y up, +z forward.

Sweet Home 3D maps cm to metres via :func:`scene_builder.sh3d_to_world`, so
the bounding box returned by trimesh is in metres and the camera coords here
are in metres too.

Default view is a 3/4 isometric from south-east above, looking at the centre
of the model. Heuristic favours overview > drama: the y elevation scales with
plan diagonal, so a 30평형 apartment and a 1000평 mansion both frame nicely.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class CameraPlacement:
    position: tuple[float, float, float]
    target: tuple[float, float, float]

    def as_card_dict(self) -> dict[str, dict[str, float]]:
        return {
            "camera_position": {
                "x": round(self.position[0], 3),
                "y": round(self.position[1], 3),
                "z": round(self.position[2], 3),
            },
            "camera_target": {
                "x": round(self.target[0], 3),
                "y": round(self.target[1], 3),
                "z": round(self.target[2], 3),
            },
        }


CAMERA_PRESETS: dict[str, tuple[float, float]] = {
    # (offset_xy_factor, offset_y_factor)  — both multiplied by plan diagonal
    "iso": (0.55, 0.95),    # default 3/4 isometric, slight zoom-out
    "iso-far": (0.85, 1.20),  # same angle, more zoom-out
    "iso-close": (0.40, 0.70),  # same angle, more zoom-in
    "top": (0.05, 1.40),    # near top-down (bird's eye)
    "side": (0.95, 0.45),   # low side angle
}


def compute_camera(
    bounds: np.ndarray | tuple, preset: str = "iso"
) -> CameraPlacement:
    """Return a CameraPlacement that frames the whole bounding box.

    Args:
        bounds: ``(bmin, bmax)`` arrays — either a ``trimesh.Scene.bounds`` or
            a tuple of ``np.ndarray``.
        preset: One of :data:`CAMERA_PRESETS` keys (``"iso"``, ``"iso-far"``,
            ``"iso-close"``, ``"top"``, ``"side"``). Defaults to ``"iso"``.

    Returns:
        Camera positioned south-east + above, targeting the model centre.
    """
    if preset not in CAMERA_PRESETS:
        raise ValueError(f"unknown camera preset {preset!r}; use one of {list(CAMERA_PRESETS)}")

    bmin = np.asarray(bounds[0], dtype=float)
    bmax = np.asarray(bounds[1], dtype=float)
    center = (bmin + bmax) / 2.0
    size = bmax - bmin
    diagonal = float(np.linalg.norm([size[0], size[2]]))

    xy_factor, y_factor = CAMERA_PRESETS[preset]
    offset_xy = diagonal * xy_factor
    offset_y = max(diagonal * y_factor, float(bmax[1]) * 3.0)

    position = (
        float(center[0]) + offset_xy,
        offset_y,
        float(center[2]) + offset_xy,
    )
    target = (float(center[0]), float(center[1]), float(center[2]))
    return CameraPlacement(position=position, target=target)


def apply_camera(config: dict[str, Any], placement: CameraPlacement) -> dict[str, Any]:
    """Insert camera_position / camera_target into a floor3d-card config dict."""
    config.update(placement.as_card_dict())
    return config
