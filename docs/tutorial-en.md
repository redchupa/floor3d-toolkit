# Tutorial — Sweet Home 3D floor plan to Home Assistant

> End-to-end: draw your apartment in Sweet Home 3D → run `floor3d-toolkit` → embed in HA `floor3d-card`.

Time: 1–2 hours one-off for drawing; 10 minutes for conversion and HA wiring.

## 0. Prerequisites

| | |
|---|---|
| Sweet Home 3D | Free GPL OSS, http://www.sweethome3d.com/ |
| Python | 3.11+ |
| Home Assistant | with `floor3d-card` installed (via HACS) |

## 1. Draw the floor plan

1. Launch Sweet Home 3D, create a new project.
2. Draw walls at real dimensions.
3. Drop in furniture from the stock catalogue.
4. **Lights are the most important step** — place one ceiling light per room/area from the `Lights` category.
5. Rename each light to something recognisable (e.g. `Living Room Main`, `Kitchen Pendant`).
6. Save as `myhome.sh3d`.

### Naming lights

`floor3d-toolkit` turns the light's name into an ASCII slug that becomes the
mesh node name in the glb. floor3d-card binds HA entities to mesh node names,
so clear names make the next step easier.

| Sweet Home 3D name | generated node | suggested HA entity |
|---|---|---|
| `Living Main Light` | `light_living_main_light` | `light.living_room_main` |
| `안방 조명` (Korean) | `light_anbang_jomyeong` | `light.master_bedroom` |
| `Kitchen LED` | `light_kitchen_led` | `light.kitchen_led` |

## 2. Install

```bash
pip install floor3d-toolkit
```

Or for development:
```bash
git clone https://github.com/redchupa/floor3d-toolkit
cd floor3d-toolkit
pip install -e ".[dev]"
```

## 3. Convert

```bash
floor3d-toolkit convert myhome.sh3d --output dist/ --name home
```

Generated files:

```
dist/
├── home.obj                       # OBJ + MTL (debugging / external tools)
├── home.mtl
├── home.glb                       # what floor3d-card reads
├── home.entity-mapping.yaml       # edit this next!
└── home.card-config.yaml          # paste into Lovelace
```

`floor3d-toolkit inspect myhome.sh3d` prints wall / furniture / light counts.

### Options

| Flag | Description |
|---|---|
| `--output / -o` | Output directory (default `dist/`) |
| `--name / -n` | Artifact base name (default: input stem) |
| `--glb-url` | URL that HA will use to serve the glb (default `/local/floor3d/home.glb`) |
| `--mapping` | User mapping YAML (step 4) |
| `--skip-furniture-meshes` | Treat furniture as bounding boxes — faster, smaller |

## 4. Edit the entity mapping

Open `home.entity-mapping.yaml`. Each mesh node has a heuristic guess:

```yaml
# floor3d-toolkit entity mapping
entities:
  light_living_main_light: light.living_main_light  # confidence 0.6 (light_ prefix)
  light_kitchen_led: light.kitchen_led              # confidence 0.6 (light_ prefix)
  furn_refrigerator: switch.refrigerator             # confidence 0.6 (keyword 'refrigerator')
  furn_sofa: null                                    # confidence 0.0 — fill me in
  door_front: null                                   # confidence 0.4 (door_/window_ prefix)
```

Replace the right-hand side with real HA `entity_id`s. Leave `null` for nodes
you don't want bound — they will be excluded from the card config.

## 5. Re-convert with the mapping

```bash
floor3d-toolkit convert myhome.sh3d \
  --output dist/ \
  --name home \
  --mapping dist/home.entity-mapping.yaml
```

`dist/home.card-config.yaml` now contains your real entity IDs.

## 6. Deploy to Home Assistant

### 6-1. Upload the glb

Copy `home.glb` to `/config/www/floor3d/` on your HA host (Samba, file editor,
SSH — whichever works).

### 6-2. Install floor3d-card (HACS)

HACS → Frontend → search `floor3d-card` → install.

### 6-3. Add the card to Lovelace

Paste the contents of `dist/home.card-config.yaml` into a new card. Confirm
`path:` + `objfile:` resolve to `/local/floor3d/home.glb`.

Refresh — your 3D floor plan appears, and toggling mapped lights changes the
mesh colours / emits light.

## 7. Troubleshooting

| Symptom | Likely cause |
|---|---|
| glb renders but clicks do nothing | The `entity_id` in the mapping YAML doesn't exist in HA |
| Furniture appears as black cubes only | Did you pass `--skip-furniture-meshes`? Or mesh extraction failed — see the `parsed:` line in the CLI output |
| Lights sit too close to the ceiling | Tweak `scene_builder.LIGHT_ELEVATION_FACTOR` (currently 0.93) for your ceiling height |
| Adding a new light shifted existing names | Same name + same scene yields `_1`, `_2` collision suffixes. Use distinct names. |

## 8. Pairing with redchupa-cards/floor3d-wrapper-card

The `floor3d-wrapper-card` in `redchupa-cards` layers an input-mode /
time-of-day rotation UI on top of floor3d-card. The card config produced here
slots straight into the wrapper.

See: https://github.com/redchupa/redchupa-cards

## 9. Privacy

The generated `.glb`/`.yaml` files describe your home's geometry. **Never
commit them to a public repository.**

This toolkit sends no data anywhere — all conversion happens locally.
