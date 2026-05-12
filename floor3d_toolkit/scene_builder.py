"""Build a `trimesh.Scene` out of a parsed :class:`Home`.

The scene is the shared in-memory representation that both the OBJ writer
and the glb exporter consume.

Coordinate convention (matches Sweet Home 3D + floor3d-card):
    SH3D uses centimetres on (x right, y forward, z up). glTF expects metres
    on (x right, y up, z forward), so ``sh3d_to_world`` flips x/y and divides
    by 100. The x flip means furniture meshes are mirrored — they're reflected
    on the X axis and re-wound before being placed.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import trimesh

from floor3d_toolkit.naming import NameAllocator, slugify
from floor3d_toolkit.sh3d_parser import Furniture, Home, Light, Wall


def sh3d_to_world(x: float, y: float, z: float) -> list[float]:
    """SH3D centimetres to glTF metres with axis remapping."""
    return [-x / 100.0, z / 100.0, -y / 100.0]


# Light boxes are intentionally tiny + emissive: only purpose is to anchor the
# floor3d-card PointLight at the right room position. 25cm matches a real
# downlight footprint without obscuring the ceiling.
LIGHT_BOX_EXTENTS = (0.25, 0.04, 0.25)
LIGHT_ELEVATION_FACTOR = 0.93  # tuck just under the ceiling slab
LIGHT_ELEVATION_OFFSET = -0.02

# Ceiling slab name is meaningful to floor3d-card: meshes prefixed with
# `transparent_slab` block PointLight rays but stay invisible to the camera.
CEILING_NAME = "transparent_slab_ceiling"
CEILING_HEIGHT = 2.40
CEILING_THICKNESS = 0.20
FLOOR_THICKNESS = 0.05
FLOOR_ELEVATION = 0.03


def build_scene(home: Home, sh3d_path: Path | None = None) -> trimesh.Scene:
    """Convert a parsed home into a positioned `trimesh.Scene`.

    Args:
        home: Parsed :class:`Home`.
        sh3d_path: Optional path to the source .sh3d. When provided, furniture
            meshes are extracted from the archive; otherwise furniture is
            represented by bounding boxes.

    Returns:
        Scene with nodes named ``wall_NNN``, ``furn_<slug>``, ``door_<slug>``,
        ``light_<slug>``, ``floor`` and ``transparent_slab_ceiling``.
    """
    scene = trimesh.Scene()

    for index, wall in enumerate(home.walls):
        _add_wall(scene, wall, index)

    allocator = NameAllocator()
    archive: zipfile.ZipFile | None = None
    if sh3d_path is not None:
        archive = zipfile.ZipFile(sh3d_path)
    try:
        for item in home.furniture:
            _add_furniture(scene, item, allocator, archive=archive)
        for light in home.lights:
            _add_light(scene, light, allocator)
    finally:
        if archive is not None:
            archive.close()

    _add_floor_and_ceiling(scene)
    return scene


def _add_wall(scene: trimesh.Scene, wall: Wall, index: int) -> None:
    length = ((wall.x_end - wall.x_start) ** 2 + (wall.y_end - wall.y_start) ** 2) ** 0.5
    if length <= 0:
        return
    cx = (wall.x_start + wall.x_end) / 2
    cy = (wall.y_start + wall.y_end) / 2
    angle = np.arctan2(wall.y_end - wall.y_start, wall.x_end - wall.x_start)

    box = trimesh.creation.box(extents=[length / 100, wall.height / 100, wall.thickness / 100])
    box.apply_transform(trimesh.transformations.rotation_matrix(-angle, [0, 1, 0]))
    box.apply_transform(
        trimesh.transformations.translation_matrix(sh3d_to_world(cx, cy, wall.height / 2))
    )
    name = f"wall_{index:03d}"
    scene.add_geometry(box, node_name=name, geom_name=name)


def _add_light(scene: trimesh.Scene, light: Light, allocator: NameAllocator) -> None:
    base = "light_" + slugify(light.name)
    name = allocator.allocate(base)
    box = trimesh.creation.box(extents=list(LIGHT_BOX_EXTENTS))
    box.apply_transform(
        trimesh.transformations.translation_matrix(
            sh3d_to_world(
                light.x,
                light.y,
                light.elevation * LIGHT_ELEVATION_FACTOR + LIGHT_ELEVATION_OFFSET,
            )
        )
    )
    scene.add_geometry(box, node_name=name, geom_name=name)


def _add_furniture(
    scene: trimesh.Scene,
    item: Furniture,
    allocator: NameAllocator,
    *,
    archive: zipfile.ZipFile | None,
) -> None:
    prefix = "door_" if item.kind == "doorOrWindow" else "furn_"
    name = allocator.allocate(prefix + slugify(item.name))

    mesh = _load_model_from_zip(archive, item.model_ref) if archive else None
    if mesh is None or len(mesh.vertices) == 0:
        mesh = trimesh.creation.box(
            extents=[item.width / 100, item.height / 100, item.depth / 100]
        )
        from_real_mesh = False
    else:
        bbox = mesh.bounding_box.extents
        if bbox[0] > 1e-6 and bbox[1] > 1e-6 and bbox[2] > 1e-6:
            mesh.apply_scale(
                [
                    (item.width / 100) / bbox[0],
                    (item.height / 100) / bbox[1],
                    (item.depth / 100) / bbox[2],
                ]
            )
        mesh.apply_translation(-mesh.bounding_box.centroid)
        # Compensate for sh3d_to_world's x flip so the extracted mesh isn't mirrored.
        reflection = np.eye(4)
        reflection[0, 0] = -1
        mesh.apply_transform(reflection)
        mesh.invert()
        # multibody=False avoids scipy.csgraph; single-body furniture is the norm here.
        mesh.fix_normals(multibody=False)
        from_real_mesh = True

    rotation_angle = item.angle if from_real_mesh else -item.angle
    mesh.apply_transform(trimesh.transformations.rotation_matrix(rotation_angle, [0, 1, 0]))
    mesh.apply_transform(
        trimesh.transformations.translation_matrix(
            sh3d_to_world(item.x, item.y, item.elevation + item.height / 2)
        )
    )
    scene.add_geometry(mesh, node_name=name, geom_name=name)


def _load_model_from_zip(
    archive: zipfile.ZipFile | None, model_ref: str | None
) -> trimesh.Trimesh | None:
    if archive is None or not model_ref:
        return None
    namelist = archive.namelist()
    data: bytes | None = None
    if model_ref in namelist:
        data = archive.read(model_ref)
    elif "/" not in model_ref:
        candidates = [n for n in namelist if n.startswith(model_ref + "/") and n.endswith(".obj")]
        if candidates:
            data = archive.read(candidates[0])
    if data is None:
        return None

    # Two flavours: raw OBJ bytes, or a zip-of-OBJ.
    try:
        mesh = trimesh.load(io.BytesIO(data), file_type="obj", force="mesh", process=False)
        if hasattr(mesh, "vertices") and len(mesh.vertices) > 0:
            return mesh
    except Exception:
        pass
    try:
        inner = zipfile.ZipFile(io.BytesIO(data))
        for n in inner.namelist():
            if n.endswith(".obj"):
                mesh = trimesh.load(
                    io.BytesIO(inner.read(n)), file_type="obj", force="mesh", process=False
                )
                if hasattr(mesh, "vertices") and len(mesh.vertices) > 0:
                    return mesh
    except Exception:
        pass
    return None


def _add_floor_and_ceiling(scene: trimesh.Scene) -> None:
    if not scene.geometry:
        return
    bbox_min, bbox_max = scene.bounds
    cx = (bbox_min[0] + bbox_max[0]) / 2
    cz = (bbox_min[2] + bbox_max[2]) / 2
    sx = bbox_max[0] - bbox_min[0] + 1.0
    sz = bbox_max[2] - bbox_min[2] + 1.0

    floor = trimesh.creation.box(extents=[sx, FLOOR_THICKNESS, sz])
    floor.apply_transform(trimesh.transformations.translation_matrix([cx, FLOOR_ELEVATION, cz]))
    scene.add_geometry(floor, node_name="floor", geom_name="floor")

    ceiling = trimesh.creation.box(extents=[sx, CEILING_THICKNESS, sz])
    ceiling.apply_transform(trimesh.transformations.translation_matrix([cx, CEILING_HEIGHT, cz]))
    scene.add_geometry(ceiling, node_name=CEILING_NAME, geom_name=CEILING_NAME)
