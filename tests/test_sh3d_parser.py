"""Tests for the .sh3d archive parser.

The fixture is a synthetic Home.xml string wrapped into an in-memory zip — no
real Sweet Home 3D file required, no personal floor plan touched.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest

from floor3d_toolkit import sh3d_parser

SAMPLE_HOME_XML = """<?xml version='1.0' encoding='UTF-8' standalone='no'?>
<home>
  <wall id='w0' xStart='0' yStart='0' xEnd='400' yEnd='0' height='230' thickness='7.5'/>
  <wall id='w1' xStart='400' yStart='0' xEnd='400' yEnd='300' height='230' thickness='7.5'/>
  <pieceOfFurniture id='f0' name='Bed' model='12'
                    x='100' y='150' elevation='0'
                    width='160' depth='200' height='45' angle='0'/>
  <doorOrWindow id='d0' name='Front Door' model='3'
                x='200' y='0' elevation='0'
                width='90' depth='10' height='210' angle='0'/>
  <light id='l0' name='Living Main Light'
         x='200' y='150' elevation='230'
         width='10' depth='10' height='10'
         color='0xFFFFE0'/>
</home>
"""


def _make_sh3d(tmp_path: Path) -> Path:
    target = tmp_path / "fake.sh3d"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Home.xml", SAMPLE_HOME_XML)
    target.write_bytes(buf.getvalue())
    return target


def test_parse_returns_walls_furniture_lights(tmp_path: Path) -> None:
    home = sh3d_parser.parse(_make_sh3d(tmp_path))
    assert len(home.walls) == 2
    assert len(home.furniture) == 2  # bed + door
    assert len(home.lights) == 1
    bed = next(f for f in home.furniture if f.name == "Bed")
    assert bed.kind == "pieceOfFurniture"
    assert bed.width == pytest.approx(160)
    door = next(f for f in home.furniture if f.kind == "doorOrWindow")
    assert door.name == "Front Door"
    light = home.lights[0]
    assert light.name == "Living Main Light"
    assert light.color == 0xFFFFE0


def test_parse_missing_home_xml_raises(tmp_path: Path) -> None:
    target = tmp_path / "empty.sh3d"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("not_home.txt", "nope")
    target.write_bytes(buf.getvalue())
    with pytest.raises(KeyError):
        sh3d_parser.parse(target)
