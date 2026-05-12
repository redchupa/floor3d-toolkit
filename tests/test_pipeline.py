"""End-to-end pipeline test on a synthetic in-memory .sh3d."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import yaml
from typer.testing import CliRunner

from floor3d_toolkit.cli import app
from tests.test_sh3d_parser import SAMPLE_HOME_XML


def _make_sh3d(tmp_path: Path) -> Path:
    target = tmp_path / "sample.sh3d"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("Home.xml", SAMPLE_HOME_XML)
    target.write_bytes(buf.getvalue())
    return target


def test_convert_writes_all_artifacts(tmp_path: Path) -> None:
    sh3d = _make_sh3d(tmp_path)
    out = tmp_path / "dist"
    # Write a mapping so the card config has at least one explicit entity.
    mapping_in = tmp_path / "mapping.yaml"
    mapping_in.write_text(
        "entities:\n  light_living_main_light: light.living_main\n",
        encoding="utf-8",
    )
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "convert",
            str(sh3d),
            "--output",
            str(out),
            "--skip-furniture-meshes",  # synthetic file has no embedded OBJ models
            "--mapping",
            str(mapping_in),
        ],
    )
    assert result.exit_code == 0, result.output

    base = sh3d.stem
    obj = out / f"{base}.obj"
    glb = out / f"{base}.glb"
    mapping = out / f"{base}.entity-mapping.yaml"
    card = out / f"{base}.card-config.yaml"
    assert obj.exists() and obj.stat().st_size > 0
    assert glb.exists() and glb.stat().st_size > 0
    assert mapping.exists() and mapping.stat().st_size > 0
    assert card.exists() and card.stat().st_size > 0

    parsed = yaml.safe_load(card.read_text(encoding="utf-8"))
    assert parsed["type"] == "custom:floor3d-card"
    entities = parsed["entities"]
    assert any(e["entity"] == "light.living_main" for e in entities)


def test_inspect_runs_without_error(tmp_path: Path) -> None:
    sh3d = _make_sh3d(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["inspect", str(sh3d)])
    assert result.exit_code == 0, result.output
    assert "walls" in result.output
