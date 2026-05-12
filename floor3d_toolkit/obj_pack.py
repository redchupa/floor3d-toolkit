"""Package Sweet Home 3D ExportToHASS output (OBJ + MTL + textures) into a
single GLB with textures embedded.

Sweet Home 3D ships a built-in HASS exporter that produces, for a project named
``home``::

    home.obj            (Wavefront geometry)
    home.mtl            (material definitions)
    home_<*>.jpeg       (referenced textures)
    home.json           (mesh-node → object_id mapping for floor3d-card)

That bundle reproduces the look of the SH3D editor 1:1, but distributing it to
floor3d-card means hosting 15+ files. This module collapses it into a single
``home.glb`` (textures embedded as glTF binary chunks). The mesh-node names —
which floor3d-card uses for entity binding — are preserved verbatim from the
input OBJ.
"""

from __future__ import annotations

from pathlib import Path

import trimesh
from trimesh.visual.material import PBRMaterial


def _ensure_emissive_baseline(
    scene: trimesh.Scene,
    factor: float = 0.18,
    show_light_fixtures: bool = False,
) -> None:
    """Stamp baseline emissive on every mesh so the GLB stays readable when
    Home Assistant light entities are off.

    Sweet Home 3D's MTL output uses ``Ka`` (ambient) to keep surfaces visible
    in dim scenes. PBR's glTF spec has no ambient term — we approximate it
    with a small ``emissiveFactor`` derived from the existing base colour.

    Args:
        scene: The packed scene whose meshes get their materials rewritten.
        factor: Base-colour fraction applied as ``emissiveFactor`` on
            non-fixture meshes.
        show_light_fixtures: When ``False`` (default), ``light_*`` mesh boxes
            are made fully transparent — they still anchor the floor3d-card
            PointLights but disappear from view, matching the look produced
            by Sweet Home 3D's own ExportToHASS exporter. When ``True``, the
            fixture boxes stay visible (useful while wiring up the
            ``entity-mapping.yaml`` so you can see which room each light
            covers).
    """
    for name, mesh in scene.geometry.items():
        material = getattr(mesh.visual, "material", None)
        base: tuple[float, float, float] = (0.9, 0.9, 0.9)
        if material is not None:
            color_attr = getattr(material, "baseColorFactor", None) or getattr(
                material, "diffuse", None
            )
            if color_attr is not None and len(color_attr) >= 3:
                rgb = list(color_attr)[:3]
                if any(c > 1.0 for c in rgb):
                    rgb = [c / 255.0 for c in rgb]
                base = tuple(rgb)

        is_light = name.lower().startswith("light")
        alpha = 1.0
        if is_light:
            if show_light_fixtures:
                emissive = [min(1.0, c + 0.4) for c in base]
            else:
                emissive = [0.0, 0.0, 0.0]
                alpha = 0.0  # invisible but still raycastable for click/click events
        else:
            emissive = [c * factor for c in base]

        rgba = [*base, alpha]
        mesh.visual = trimesh.visual.TextureVisuals(
            material=PBRMaterial(
                name=name,
                baseColorFactor=rgba,
                emissiveFactor=emissive,
                metallicFactor=0.0,
                roughnessFactor=0.85,
                alphaMode="BLEND" if alpha < 1.0 else "OPAQUE",
                baseColorTexture=getattr(material, "baseColorTexture", None),
            )
        )


def pack(
    obj_path: Path,
    glb_path: Path,
    *,
    emissive_factor: float = 0.18,
    show_light_fixtures: bool = False,
) -> Path:
    """Convert an OBJ + MTL + textures bundle into a single embedded GLB.

    Args:
        obj_path: Path to the .obj file. ``.mtl`` and any texture files it
            references must sit next to it on disk.
        glb_path: Destination .glb. Parent directories are created if needed.
        emissive_factor: Fraction of base colour stamped as ``emissiveFactor``
            on each non-light mesh so the scene reads even without HA lights
            switched on. Set to ``0`` to ship pure base colour.
        show_light_fixtures: When ``False`` (default), ``light_*`` meshes are
            made fully transparent — they still anchor the floor3d-card
            PointLights but disappear from view. Set to ``True`` during
            entity-mapping work so you can see fixture positions.

    Returns:
        The path written.

    Raises:
        FileNotFoundError: when ``obj_path`` does not exist.
        ValueError: when the file did not contain any exportable geometry.
    """
    obj_path = Path(obj_path)
    if not obj_path.exists():
        raise FileNotFoundError(obj_path)
    glb_path = Path(glb_path)
    glb_path.parent.mkdir(parents=True, exist_ok=True)

    loaded = trimesh.load(str(obj_path), force=None)
    scene = loaded if isinstance(loaded, trimesh.Scene) else trimesh.Scene(loaded)
    if not scene.geometry:
        raise ValueError(f"no geometry found in {obj_path.name}")

    if emissive_factor > 0:
        _ensure_emissive_baseline(
            scene,
            factor=emissive_factor,
            show_light_fixtures=show_light_fixtures,
        )

    scene.export(str(glb_path), file_type="glb")
    return glb_path
