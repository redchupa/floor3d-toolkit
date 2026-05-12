"""Convert a `trimesh.Scene` (or OBJ on disk) to glTF 2.0 binary (.glb).

floor3d-card is a Three.js custom card and reads node names from the glb's
glTF nodes — so we use trimesh's native exporter, which preserves the
``node_name`` we set in :mod:`floor3d_toolkit.scene_builder`.
"""

from __future__ import annotations

from pathlib import Path

import trimesh


def export_scene(scene: trimesh.Scene, glb_path: Path) -> Path:
    """Write ``scene`` as a glb file. Returns the path written."""
    glb_path = Path(glb_path)
    glb_path.parent.mkdir(parents=True, exist_ok=True)
    scene.export(glb_path, file_type="glb")
    return glb_path


def convert(obj_path: Path, glb_path: Path) -> Path:
    """Convert an existing OBJ on disk to glb.

    This is a convenience wrapper for users who already have an .obj and only
    want the glb. The full pipeline (``scene_builder.build_scene`` →
    ``export_scene``) avoids the OBJ round-trip and preserves vertex normals
    exactly.
    """
    scene = trimesh.load(str(obj_path))
    if isinstance(scene, trimesh.Trimesh):
        scene = trimesh.Scene(scene)
    return export_scene(scene, glb_path)
