"""Module API smoke tests — verify the planned surface is wired up."""

from __future__ import annotations

import numpy as np

from floor3d_toolkit import (
    card_config_gen,
    entity_mapper,
    light_extractor,
    obj_to_glb,
    obj_writer,
    placement,
    scene_builder,
    sh3d_parser,
)


def test_sh3d_parser_exposes_dataclasses() -> None:
    assert hasattr(sh3d_parser, "Wall")
    assert hasattr(sh3d_parser, "Furniture")
    assert hasattr(sh3d_parser, "Light")
    assert hasattr(sh3d_parser, "Home")
    assert callable(sh3d_parser.parse)


def test_scene_builder_exposes_build_scene() -> None:
    assert callable(scene_builder.build_scene)
    assert callable(scene_builder.sh3d_to_world)


def test_obj_writer_exposes_palette() -> None:
    assert callable(obj_writer.write_obj)
    palette = obj_writer.ColorPalette()
    assert palette.color_for("wall_001") == obj_writer.DEFAULT_BASE_COLORS["wall_"]


def test_obj_to_glb_exposes_export() -> None:
    assert callable(obj_to_glb.export_scene)
    assert callable(obj_to_glb.convert)


def test_entity_mapper_keyword_hit() -> None:
    [mapping] = entity_mapper.suggest_entities(["light_living_main"])
    assert mapping.entity_id == "light.living_main"
    assert mapping.confidence == 0.6


def test_entity_mapper_keyword_uses_tokens_not_substring() -> None:
    # Regression: 'ac' must not match inside 'machine'; washing machines should
    # NOT be auto-classified as climate.
    [mapping] = entity_mapper.suggest_entities(["furn_clothes_washing_machine"])
    assert mapping.entity_id is None
    assert mapping.confidence == 0.0


def test_entity_mapper_override_wins() -> None:
    rules = entity_mapper.MappingRules(by_node={"light_a": "light.bedroom_ceiling"})
    [mapping] = entity_mapper.suggest_entities(["light_a"], rules=rules)
    assert mapping.entity_id == "light.bedroom_ceiling"
    assert mapping.confidence == 1.0


def test_entity_mapper_explicit_null_opt_out() -> None:
    # Regression: when user writes `light_xyz: null` in mapping.yaml they mean
    # "skip this node", not "fall through to heuristic".
    rules = entity_mapper.MappingRules(by_node={"light_xyz": None})
    [mapping] = entity_mapper.suggest_entities(["light_xyz"], rules=rules)
    assert mapping.entity_id is None
    assert mapping.confidence == 1.0
    assert "opted out" in mapping.reason


def test_card_config_min_confidence_filters_suggestions(tmp_path) -> None:
    # Default min_confidence=1.0 drops auto-suggested entries; only explicit
    # user overrides go into the card.
    mappings = [
        entity_mapper.EntityMapping("light_a", "light.a", 1.0, "user override"),
        entity_mapper.EntityMapping("furn_tv", "media_player.tv", 0.6, "keyword 'tv'"),
    ]
    out = tmp_path / "card.yaml"
    config = card_config_gen.build_config("/local/x.glb", mappings, [], out, name="Demo")
    entity_ids = [e["entity"] for e in config["entities"]]
    assert "light.a" in entity_ids
    assert "media_player.tv" not in entity_ids


def test_light_extractor_uses_slug_and_collision_suffix() -> None:
    Light = sh3d_parser.Light  # noqa: N806
    lights = [
        Light(id="l1", name="Master Bedroom Light", model_ref=None, x=0, y=0, elevation=230,
              width=10, depth=10, height=10),
        Light(id="l2", name="Master Bedroom Light", model_ref=None, x=10, y=0, elevation=230,
              width=10, depth=10, height=10),
    ]
    out = light_extractor.extract(lights)
    assert out[0].mesh_node.startswith("light_")
    assert out[1].mesh_node != out[0].mesh_node


def test_placement_compute_camera_frames_model() -> None:
    bounds = (np.array([-14.0, 0.0, -10.5]), np.array([0.5, 2.5, 0.0]))
    cam = placement.compute_camera(bounds)
    # Camera target sits at the geometric centre.
    assert cam.target == (-6.75, 1.25, -5.25)
    # Camera position is above and offset away from origin so the model fits frame.
    assert cam.position[1] > bounds[1][1]


def test_card_config_gen_writes_yaml(tmp_path) -> None:
    mappings = [
        entity_mapper.EntityMapping(
            source_name="light_living",
            entity_id="light.living",
            confidence=1.0,
            reason="user override",
        )
    ]
    candidates = [
        light_extractor.LightCandidate(
            mesh_node="light_living",
            suggested_entity_id="light.living",
            x_cm=0,
            y_cm=0,
            elevation_cm=230,
            color_hex="#ffffff",
        )
    ]
    out = tmp_path / "card.yaml"
    config = card_config_gen.build_config(
        "/local/floor3d/home.glb", mappings, candidates, out, name="Demo"
    )
    assert out.exists()
    assert config["objfile"] == "home.glb"
    assert config["entities"][0]["object_id"] == "light_living"
    assert config["entities"][0]["type3d"] == "light"
