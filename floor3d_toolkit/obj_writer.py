"""Write a `trimesh.Scene` into Wavefront OBJ + MTL files with vertex normals.

floor3d-card relies on:
- per-mesh ``usemtl`` so each object can be recoloured/illuminated independently;
- ``vn`` vertex normals (with ``f a//a`` face syntax) so PointLight shading works;
- emissive ``Ke`` materials for ``light_*`` meshes so they glow even when the
  scene's global light is dim;
- standard diffuse for everything else.

This module is intentionally palette-agnostic — colours are chosen by mesh name
prefix only, and the default palette can be overridden by passing a
:class:`ColorPalette`.

:func:`apply_palette_to_scene` also stamps materials onto the live
``trimesh.Scene`` so that ``Scene.export('.glb')`` ships real colours, not
trimesh's default grey.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import trimesh
from trimesh.visual.material import PBRMaterial

RGB = tuple[int, int, int]


DEFAULT_BASE_COLORS: dict[str, RGB] = {
    # White-tone uniform palette. Walls + floor same colour, dark accents
    # (TV / piano / monitor) provide visual contrast.
    "wall_": (240, 238, 234),
    "floor": (240, 238, 234),
    "light_": (255, 245, 215),
    "door_": (220, 225, 230),
    "transparent_slab": (15, 15, 25),
}

# Keyword -> diffuse for ``furn_*`` meshes. First match wins; keep order
# specific-before-general so e.g. "bedside" matches before "bed".
DEFAULT_FURNITURE_KEYWORDS: tuple[tuple[tuple[str, ...], RGB], ...] = (
    (("toilet", "japanese"), (248, 248, 245)),
    (("washbasin", "basin"), (235, 240, 245)),
    (("bathtub", "shower", "jet"), (220, 230, 238)),
    (("mirror",), (215, 230, 240)),
    (("refrigerator", "refridgerator"), (225, 225, 232)),
    (("dishwasher",), (210, 215, 222)),
    (("washing", "machine"), (228, 230, 235)),
    (("cooker", "induction"), (70, 70, 78)),
    (("hood",), (90, 90, 100)),
    (("microwave",), (55, 55, 62)),
    (("toaster",), (165, 165, 172)),
    (("wardrobe",), (190, 155, 115)),
    (("cabinet", "drawer", "pensile", "upper"), (210, 195, 170)),
    (("bedside",), (165, 125, 90)),
    (("bed",), (235, 215, 195)),
    (("piano", "upright"), (30, 22, 20)),
    (("island",), (175, 140, 100)),
    (("table", "tavolo", "desk", "wood"), (155, 115, 80)),
    (("sofa", "couch"), (100, 95, 100)),
    (("flat", "tv", "monitor", "lcd", "screen", "intercom"), (28, 28, 34)),
)

_DEFAULT_FURNITURE_FALLBACK: RGB = (165, 135, 105)
_DEFAULT_UNKNOWN: RGB = (200, 200, 200)


@dataclass(frozen=True)
class ColorPalette:
    base: Mapping[str, RGB] = field(default_factory=lambda: DEFAULT_BASE_COLORS)
    furniture_keywords: Iterable[tuple[tuple[str, ...], RGB]] = field(
        default_factory=lambda: DEFAULT_FURNITURE_KEYWORDS
    )
    furniture_fallback: RGB = _DEFAULT_FURNITURE_FALLBACK
    unknown: RGB = _DEFAULT_UNKNOWN

    def color_for(self, mesh_name: str) -> RGB:
        for prefix, rgb in self.base.items():
            if mesh_name.startswith(prefix) or mesh_name == prefix.rstrip("_"):
                return rgb
        if mesh_name.startswith("furn_"):
            low = mesh_name.lower()
            for keys, rgb in self.furniture_keywords:
                if any(k in low for k in keys):
                    return rgb
            return self.furniture_fallback
        return self.unknown


def apply_palette_to_scene(
    scene: trimesh.Scene, palette: ColorPalette | None = None
) -> None:
    """Stamp a PBRMaterial on each scene mesh so glb export keeps real colours.

    Without this, ``Scene.export('.glb')`` ships every mesh with trimesh's
    grey default and the model looks dark/flat in floor3d-card.

    Walls and furniture get a small ``emissiveFactor`` so they stay visible
    even when every HA light entity is OFF. Without this baseline, vertical
    surfaces collapse to near-black because floor3d-card's default sun light
    only hits horizontal ones.
    """
    palette = palette or ColorPalette()
    for name, mesh in scene.geometry.items():
        r, g, b = palette.color_for(name)
        rgba = [r / 255.0, g / 255.0, b / 255.0, 1.0]
        if name.startswith("light_"):
            emissive = rgba[:3]  # fully self-illuminated
        elif name == "transparent_slab_ceiling":
            emissive = [0.0, 0.0, 0.0]
        else:
            # 12% baseline — Sweet Home 3D ExportToHASS look: ambient pickup
            # is mostly from directional/PointLights, walls/floor only weakly
            # self-emit so coloured furniture stays readable.
            emissive = [c * 0.12 for c in rgba[:3]]
        mesh.visual = trimesh.visual.TextureVisuals(
            material=PBRMaterial(
                name=name,
                baseColorFactor=rgba,
                emissiveFactor=emissive,
                metallicFactor=0.0,
                roughnessFactor=0.85,
            )
        )


def _flatten_scene(scene: trimesh.Scene) -> dict[str, trimesh.Trimesh]:
    """Bake each node's transform into its mesh and key by node name."""
    out: dict[str, trimesh.Trimesh] = {}
    base = scene.graph.base_frame
    for node in scene.graph.nodes:
        if node == base:
            continue
        transform, geom_name = scene.graph[node]
        if not geom_name or geom_name not in scene.geometry:
            continue
        mesh = scene.geometry[geom_name].copy()
        mesh.apply_transform(transform)
        if len(mesh.vertices) > 0 and len(mesh.faces) > 0:
            out[node] = mesh
    return out


def write_obj(
    scene: trimesh.Scene,
    obj_path: Path,
    mtl_path: Path | None = None,
    *,
    palette: ColorPalette | None = None,
) -> list[str]:
    """Serialise ``scene`` to ``obj_path`` (+ matching .mtl).

    Returns:
        The list of mesh node names that were written, in file order. Callers
        use this list to build entity-mapping YAML or floor3d-card configs.
    """
    obj_path = Path(obj_path)
    if mtl_path is None:
        mtl_path = obj_path.with_suffix(".mtl")
    palette = palette or ColorPalette()

    meshes = _flatten_scene(scene)
    if not meshes:
        raise ValueError("Scene contained no exportable geometry.")

    obj_lines: list[str] = [
        "# Generated by floor3d-toolkit",
        f"mtllib {mtl_path.name}",
        "",
    ]
    written: list[str] = []
    vertex_offset = 0
    for name, mesh in meshes.items():
        written.append(name)
        obj_lines.append(f"o {name}")
        obj_lines.append(f"usemtl {name}")
        normals = mesh.vertex_normals
        for v in mesh.vertices:
            obj_lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
        for n in normals:
            obj_lines.append(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}")
        for face in mesh.faces:
            a = face[0] + vertex_offset + 1
            b = face[1] + vertex_offset + 1
            c = face[2] + vertex_offset + 1
            obj_lines.append(f"f {a}//{a} {b}//{b} {c}//{c}")
        vertex_offset += len(mesh.vertices)
        obj_lines.append("")

    obj_path.write_text("\n".join(obj_lines), encoding="utf-8")
    mtl_path.write_text(_render_mtl(written, palette), encoding="utf-8")
    return written


def _render_mtl(mesh_names: list[str], palette: ColorPalette) -> str:
    out: list[str] = ["# Generated by floor3d-toolkit", ""]
    for name in mesh_names:
        r, g, b = palette.color_for(name)
        out.append(f"newmtl {name}")
        if name.startswith("light_"):
            out.append("Ke 1.0 1.0 1.0")
            out.append(f"Kd {r/255:.4f} {g/255:.4f} {b/255:.4f}")
            out.append("Ka 0.5 0.5 0.5")
        else:
            out.append(f"Kd {r/255:.4f} {g/255:.4f} {b/255:.4f}")
            out.append("Ka 0.05 0.05 0.05")
        out.append("Ks 0 0 0")
        out.append("Ns 10")
        out.append("illum 2")
        out.append("d 1")
        out.append("")
    return "\n".join(out)
