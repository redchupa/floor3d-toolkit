"""Extract Sweet Home 3D point lights as HA ``light.*`` candidates."""

from __future__ import annotations

from dataclasses import dataclass

from floor3d_toolkit.naming import NameAllocator, slugify
from floor3d_toolkit.sh3d_parser import Light


@dataclass(frozen=True)
class LightCandidate:
    """A SH3D point light proposed as a HA `light.*` entity."""

    mesh_node: str
    suggested_entity_id: str
    x_cm: float
    y_cm: float
    elevation_cm: float
    color_hex: str


def _color_hex(color_int: int) -> str:
    return f"#{color_int & 0xFFFFFF:06x}"


def extract(lights: list[Light]) -> list[LightCandidate]:
    """Produce HA light entity candidates from parsed point lights.

    Mesh node naming matches :func:`floor3d_toolkit.scene_builder._add_light`:
    ``light_<slug>`` with collision suffix for duplicates.
    """
    allocator = NameAllocator()
    out: list[LightCandidate] = []
    for light in lights:
        slug = slugify(light.name)
        node = allocator.allocate("light_" + slug)
        out.append(
            LightCandidate(
                mesh_node=node,
                suggested_entity_id=f"light.{slug}",
                x_cm=light.x,
                y_cm=light.y,
                elevation_cm=light.elevation,
                color_hex=_color_hex(light.color),
            )
        )
    return out
