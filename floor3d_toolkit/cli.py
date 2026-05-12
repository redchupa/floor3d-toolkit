"""Command-line interface for floor3d-toolkit.

Usage:
    floor3d-toolkit convert input.sh3d --output dist/
    floor3d-toolkit inspect input.sh3d
    floor3d-toolkit version
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from floor3d_toolkit import __version__
from floor3d_toolkit.card_config_gen import build_config
from floor3d_toolkit.entity_mapper import MappingRules, dump_entity_mapping_yaml, suggest_entities
from floor3d_toolkit.light_extractor import extract as extract_lights
from floor3d_toolkit.obj_pack import pack as pack_obj_bundle
from floor3d_toolkit.obj_to_glb import export_scene
from floor3d_toolkit.obj_writer import apply_palette_to_scene, write_obj
from floor3d_toolkit.scene_builder import build_scene
from floor3d_toolkit.sh3d_parser import parse

app = typer.Typer(
    name="floor3d-toolkit",
    help="Sweet Home 3D (.sh3d) -> HA floor3d-card pipeline.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _mask_path(p: Path) -> str:
    """Path string with the OS username masked (CLAUDE.md §0)."""
    try:
        rel = p.resolve().relative_to(Path.home())
        return f"~/{rel.as_posix()}"
    except ValueError:
        return p.name


@app.command()
def version() -> None:
    """Print the package version."""
    console.print(f"floor3d-toolkit {__version__}")


@app.command()
def convert(
    input_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a Sweet Home 3D .sh3d file.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            file_okay=False,
            dir_okay=True,
            writable=True,
            help="Output directory for .glb and generated YAML.",
        ),
    ] = Path("dist"),
    name: Annotated[
        str | None,
        typer.Option("--name", "-n", help="Base name for generated artifacts (default: input stem)."),
    ] = None,
    glb_url: Annotated[
        str,
        typer.Option(
            "--glb-url",
            help="URL Home Assistant will use to serve the .glb (e.g. /local/floor3d/home.glb).",
        ),
    ] = "/local/floor3d/home.glb",
    mapping_yaml: Annotated[
        Path | None,
        typer.Option(
            "--mapping",
            exists=True,
            file_okay=True,
            dir_okay=False,
            help="Optional YAML with `entities:` overrides keyed by mesh node name.",
        ),
    ] = None,
    skip_furniture_meshes: Annotated[
        bool,
        typer.Option(
            "--skip-furniture-meshes",
            help="Treat furniture as bounding boxes; skips heavy mesh extraction.",
        ),
    ] = False,
    camera_preset: Annotated[
        str,
        typer.Option(
            "--camera",
            help="Camera angle preset: iso | iso-far | iso-close | top | side.",
        ),
    ] = "iso",
    light_preset: Annotated[
        str,
        typer.Option(
            "--light-preset",
            help="Per-light defaults preset: warm | warm-bright | cool | daylight | subtle.",
        ),
    ] = "warm",
) -> None:
    """Convert a .sh3d file into glb + entity-mapping + card-config artifacts."""
    output.mkdir(parents=True, exist_ok=True)
    base = name or input_file.stem
    console.print(f"[bold]Source:[/bold] {_mask_path(input_file)}")
    console.print(f"[bold]Output:[/bold] {_mask_path(output)}")

    home = parse(input_file)
    console.print(
        f"  parsed: walls={len(home.walls)} furniture={len(home.furniture)} lights={len(home.lights)}"
    )

    scene_source = None if skip_furniture_meshes else input_file
    scene = build_scene(home, sh3d_path=scene_source)
    console.print(f"  scene meshes: {len(scene.geometry)}")

    obj_path = output / f"{base}.obj"
    glb_path = output / f"{base}.glb"
    mapping_path = output / f"{base}.entity-mapping.yaml"
    card_path = output / f"{base}.card-config.yaml"

    node_names = write_obj(scene, obj_path)
    apply_palette_to_scene(scene)
    export_scene(scene, glb_path)

    rules = MappingRules.from_yaml(mapping_yaml) if mapping_yaml else None
    mappings = suggest_entities(node_names, rules=rules)
    dump_entity_mapping_yaml(mappings, mapping_path)

    candidates = extract_lights(home.lights)
    build_config(
        glb_url,
        mappings,
        candidates,
        card_path,
        name=base,
        scene_bounds=scene.bounds,
        camera_preset=camera_preset,
        light_preset=light_preset,
    )

    console.print(f"  obj  -> {_mask_path(obj_path)}")
    console.print(f"  glb  -> {_mask_path(glb_path)}")
    console.print(f"  yaml -> {_mask_path(mapping_path)}")
    console.print(f"  card -> {_mask_path(card_path)}")
    console.print("[green]done.[/green]")


@app.command()
def pack(
    obj_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="OBJ file from Sweet Home 3D's 'Export to Home Assistant'. "
            "MTL + textures must be alongside it.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Destination .glb path.",
        ),
    ] = Path("dist/home.glb"),
    show_light_fixtures: Annotated[
        bool,
        typer.Option(
            "--show-light-fixtures/--hide-light-fixtures",
            help="Show small fixture boxes at each light position. Defaults to "
            "hidden for a clean final look; turn on while wiring up "
            "entity-mapping.yaml so you can see where each light sits.",
        ),
    ] = False,
) -> None:
    """Pack an ExportToHASS OBJ bundle into a single GLB with textures embedded."""
    console.print(f"[bold]Source:[/bold] {_mask_path(obj_file)}")
    written = pack_obj_bundle(obj_file, output, show_light_fixtures=show_light_fixtures)
    size_mb = written.stat().st_size / (1024 * 1024)
    console.print(f"  glb  -> {_mask_path(written)}  ({size_mb:.1f} MB)")
    console.print(
        f"  light fixtures: {'visible' if show_light_fixtures else 'hidden (transparent)'}"
    )
    console.print("[green]done.[/green]")


@app.command()
def inspect(
    input_file: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Path to a Sweet Home 3D .sh3d file.",
        ),
    ],
) -> None:
    """Print a summary of walls, furniture, and lights inside a .sh3d file."""
    console.print(f"[bold]Source:[/bold] {_mask_path(input_file)}")
    home = parse(input_file)

    summary = Table(title="Home contents", show_lines=False)
    summary.add_column("Category", style="bold")
    summary.add_column("Count", justify="right")
    summary.add_row("walls", str(len(home.walls)))
    summary.add_row("furniture", str(len(home.furniture)))
    summary.add_row("doors / windows", str(sum(1 for f in home.furniture if f.kind == "doorOrWindow")))
    summary.add_row("lights", str(len(home.lights)))
    console.print(summary)

    if home.lights:
        console.print("[bold]Lights:[/bold]")
        for light in home.lights:
            console.print(f"  - {light.name or '(unnamed)'}  elev={light.elevation:.0f}cm")


if __name__ == "__main__":
    app()
