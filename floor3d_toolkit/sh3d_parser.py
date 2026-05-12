"""Parse Sweet Home 3D `.sh3d` archives into a structured intermediate model.

A `.sh3d` file is a ZIP archive whose entries include:
    Home                 (XML — rooms, walls, furniture, lights, cameras)
    Home.entries         (metadata)
    <model-*>.obj/.mtl   (referenced 3D models, sometimes embedded as inner zips)
    <texture-*>.png/.jpg (referenced textures)

The XML inside is single-quoted attribute-only form, e.g.::

    <wall id='wall0' xStart='0' yStart='0' xEnd='400' yEnd='0'
          height='230' thickness='7.5'/>
    <pieceOfFurniture id='f0' name='Bed' model='12'
                      x='100' y='200' elevation='0'
                      width='160' depth='200' height='45' angle='0'/>

Reference (Sweet Home 3D is GPL OSS):
    http://www.sweethome3d.com/userGuide.jsp
"""

from __future__ import annotations

import contextlib
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# Attributes inside Home.xml are single-quoted: name='value'
_ATTR_RE = re.compile(r"(\w+)='([^']*)'")


def _parse_attrs(tag: str) -> dict[str, str]:
    return {m.group(1): m.group(2) for m in _ATTR_RE.finditer(tag)}


def _float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Wall:
    id: str
    x_start: float
    y_start: float
    x_end: float
    y_end: float
    thickness: float
    height: float


@dataclass(frozen=True)
class Room:
    id: str
    name: str | None
    polygon: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class Furniture:
    id: str
    name: str
    kind: str  # "pieceOfFurniture" | "doorOrWindow"
    model_ref: str | None
    x: float
    y: float
    elevation: float
    width: float
    depth: float
    height: float
    angle: float = 0.0


@dataclass(frozen=True)
class Light:
    id: str
    name: str
    model_ref: str | None
    x: float
    y: float
    elevation: float
    width: float
    depth: float
    height: float
    angle: float = 0.0
    power: float = 1.0
    color: int = 0xFFFFFF


@dataclass
class Home:
    walls: list[Wall] = field(default_factory=list)
    rooms: list[Room] = field(default_factory=list)
    furniture: list[Furniture] = field(default_factory=list)
    lights: list[Light] = field(default_factory=list)


def _iter_tags(xml: str, tag: str):
    """Yield each `<tag .../>` and `<tag ...>...</tag>` opening attribute string."""
    yield from (m.group(0) for m in re.finditer(rf"<{tag}\s[^>]*?/>", xml))
    for m in re.finditer(rf"<{tag}\s[^>]*?>.*?</{tag}>", xml, re.DOTALL):
        head = m.group(0).split(">", 1)[0] + ">"
        yield head


def parse(sh3d_path: Path) -> Home:
    """Parse a .sh3d archive into a :class:`Home` model.

    Args:
        sh3d_path: Path to a Sweet Home 3D project file.

    Returns:
        A populated :class:`Home` describing walls, rooms, furniture, and lights.

    Raises:
        FileNotFoundError: when ``sh3d_path`` does not exist.
        zipfile.BadZipFile: when the file is not a valid zip archive.
        KeyError: when ``Home.xml`` (case variants) is missing inside the archive.
    """
    sh3d_path = Path(sh3d_path)
    with zipfile.ZipFile(sh3d_path) as z:
        # Sweet Home 3D writes either "Home" or "Home.xml" depending on version.
        names = z.namelist()
        for candidate in ("Home.xml", "Home"):
            if candidate in names:
                home_xml = z.read(candidate).decode("utf-8")
                break
        else:
            raise KeyError(f"Home.xml not found in {sh3d_path.name}")

    home = Home()

    for raw in _iter_tags(home_xml, "wall"):
        a = _parse_attrs(raw)
        try:
            home.walls.append(
                Wall(
                    id=a.get("id", f"wall_{len(home.walls)}"),
                    x_start=float(a["xStart"]),
                    y_start=float(a["yStart"]),
                    x_end=float(a["xEnd"]),
                    y_end=float(a["yEnd"]),
                    thickness=_float(a.get("thickness"), 7.5),
                    height=_float(a.get("height"), 230.0),
                )
            )
        except (KeyError, ValueError):
            continue

    for raw in _iter_tags(home_xml, "pieceOfFurniture"):
        _append_furniture(home, raw, kind="pieceOfFurniture")
    for raw in _iter_tags(home_xml, "doorOrWindow"):
        _append_furniture(home, raw, kind="doorOrWindow")

    for raw in _iter_tags(home_xml, "light"):
        a = _parse_attrs(raw)
        try:
            home.lights.append(
                Light(
                    id=a.get("id", f"light_{len(home.lights)}"),
                    name=a.get("name", ""),
                    model_ref=a.get("model"),
                    x=float(a["x"]),
                    y=float(a["y"]),
                    elevation=_float(a.get("elevation"), 0.0),
                    width=_float(a.get("width"), 10.0),
                    depth=_float(a.get("depth"), 10.0),
                    height=_float(a.get("height"), 10.0),
                    angle=_float(a.get("angle"), 0.0),
                    power=_float(a.get("power"), 1.0),
                    color=int(a.get("color", "0xFFFFFF"), 16) if a.get("color") else 0xFFFFFF,
                )
            )
        except (KeyError, ValueError):
            continue

    return home


def _append_furniture(home: Home, raw: str, *, kind: str) -> None:
    a = _parse_attrs(raw)
    with contextlib.suppress(KeyError, ValueError):
        home.furniture.append(
            Furniture(
                id=a.get("id", f"{kind}_{len(home.furniture)}"),
                name=a.get("name", ""),
                kind=kind,
                model_ref=a.get("model"),
                x=float(a["x"]),
                y=float(a["y"]),
                elevation=_float(a.get("elevation"), 0.0),
                width=float(a["width"]),
                depth=float(a["depth"]),
                height=float(a["height"]),
                angle=_float(a.get("angle"), 0.0),
            )
        )
