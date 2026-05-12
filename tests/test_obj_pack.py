"""Smoke test for the ExportToHASS OBJ → GLB packaging path.

Builds a tiny OBJ + MTL pair in tmp_path, packs it, and asserts the output is
a non-empty .glb that re-loads with at least one named mesh.
"""

from __future__ import annotations

from pathlib import Path

import trimesh

from floor3d_toolkit.obj_pack import pack

SAMPLE_OBJ = """# tiny cube for pack test
mtllib sample.mtl
o light_test_light
usemtl test_mtl
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
v 0 0 1
v 1 0 1
v 1 1 1
v 0 1 1
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
"""

SAMPLE_MTL = """newmtl test_mtl
Kd 0.9 0.4 0.2
Ka 0.1 0.1 0.1
Ks 0 0 0
Ns 10
illum 2
d 1
"""


def test_pack_writes_glb_with_geometry(tmp_path: Path) -> None:
    obj = tmp_path / "sample.obj"
    mtl = tmp_path / "sample.mtl"
    obj.write_text(SAMPLE_OBJ, encoding="utf-8")
    mtl.write_text(SAMPLE_MTL, encoding="utf-8")

    glb = tmp_path / "out.glb"
    pack(obj, glb)

    assert glb.exists()
    assert glb.stat().st_size > 0

    loaded = trimesh.load(str(glb))
    scene = loaded if isinstance(loaded, trimesh.Scene) else trimesh.Scene(loaded)
    assert len(scene.geometry) >= 1
