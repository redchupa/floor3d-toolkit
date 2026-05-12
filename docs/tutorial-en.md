# Tutorial — Sweet Home 3D floor plan to Home Assistant

> End-to-end: draw your home in Sweet Home 3D → export with the ExportToHASS
> plugin → package with `floor3d-toolkit` → drop into HA's `floor3d-card`.

Time budget: 1–2 hours for drawing (one-off), 10 minutes for conversion and HA wiring.

---

## Before you start — two approaches exist

There are actually **two** ways to bring a Sweet Home 3D floor plan into HA.
This tutorial covers **Approach A**.

| | Approach A — **this tutorial** (dynamic 3D) | Approach B (static PNG) |
|---|---|---|
| Plugin | `adizanni/ExportToHASS` | `shmuelzon/home-assistant-floor-plan` |
| HA card | `floor3d-card` | built-in `picture-elements` |
| Feel | rotate / zoom, real-time lighting | lightweight, ON/OFF PNG swap |
| This toolkit | **used** (`pack` command) | not used |

If you mostly want a lightweight static plan on mobile, Approach B is a
great choice. Pick Approach A when you want the interactive 3D dashboard.

---

## 0. Prerequisites

| | |
|---|---|
| Sweet Home 3D | Free / GPL — https://www.sweethome3d.com/download.jsp |
| ExportToHASS plugin (`.sh3p`) | https://github.com/adizanni/ExportToHASS/releases/latest/download/ExportToHASSPlugin.sh3p |
| Python | 3.11+ |
| Home Assistant | + [HACS](https://www.hacs.xyz/) (to install `floor3d-card`) |

### Install the ExportToHASS plugin (one-off)

1. Download `ExportToHASSPlugin.sh3p` from the URL above.
2. Launch Sweet Home 3D → `File → Preferences → Plugins`.
3. **Import...** the `.sh3p` file (or drag it onto the SH3D window).
4. Restart Sweet Home 3D.
5. Verify: `File → Export` now contains an **`Export to Home Assistant`** item.

---

## 1. Draw the plan

1. Walls at real dimensions.
2. Furniture from the stock catalogue.
3. **At least one ceiling light per room/area** from the `Lights` category.
4. Rename each light to something recognisable (e.g. `Living Main Light`).
5. Save as `myhome.sh3d`.

> ⚠️ **Use Latin (ASCII) names only inside SH3D.** The ExportToHASS plugin
> does not handle non-ASCII mesh names correctly. Korean / Japanese / etc.
> HA entity IDs are fine — only the SH3D mesh node names need to be ASCII.

The light's name becomes the GLB's mesh node name, which is what
`floor3d-card` uses as `object_id`. Clear, ASCII names = easier mapping
later.

---

## 2. Export to Home Assistant

`File → Export → Export to Home Assistant` → pick an output folder.

Outputs:
```
home.obj
home.mtl
home_<lots>.jpeg     # 14+ texture files
home.json            # mesh node -> friendly name map
```

---

## 3. Install and run floor3d-toolkit

```bash
pip install floor3d-toolkit
cd ~/Desktop/myhome_export
floor3d-toolkit pack home.obj -o dist/home.glb
```

Output:
```
dist/
├── home.glb          # texture-embedded GLB (~10 MB)
└── home.nodes.txt    # every mesh node name in the GLB
```

### Pack options

| Option | Description |
|---|---|
| `-o / --output` | Output GLB path (default `dist/home.glb`) |
| `--show-light-fixtures` | Reveal light fixture boxes (hidden by default). Useful while wiring entities |
| `--hide-light-fixtures` | Hide fixtures (default) |

---

## 4. Upload to Home Assistant

Copy `dist/home.glb` into HA's `/config/www/floor3d/` (Samba addon, File
editor addon, SCP — whichever).

---

## 5. Install floor3d-card and configure

### 5-1. Install via HACS

HACS → **Dashboard** tab → search **`floor3d-card`** (the one by `adizanni`) → click the result → **DOWNLOAD** → refresh browser.

> ⚠️ Don't confuse the two packages:
> - `adizanni/floor3d-card` — the Lovelace card you install in HACS Dashboard (this step).
> - `redchupa/floor3d-toolkit` — the PC-side Python CLI you `pip install`-ed in step 3. It is **not** an HACS plugin; adding it to HACS produces `Repository structure not compliant`.

> HACS 2.0+ exposes four categories: **Integration / Dashboard / Template / Theme**. Lovelace cards like `floor3d-card` live under **Dashboard** (the old `Frontend` label was retired).

### 5-2. Card YAML starter

Edit dashboard → add card → manual → paste:

```yaml
type: custom:floor3d-card
path: /local/floor3d/
objfile: home.glb
shadow: 'yes'
extralightmode: 'yes'
globalLightPower: 0.25
entities:
  - entity: light.living_room_main
    type3d: light
    object_id: light_living_main_light   # copy from home.nodes.txt
    action: more-info
    light:
      lumens: 1000
      color: '#ffffff'
      distance: 400
      shadow: 'yes'
      vertical_alignment: bottom
```

### 5-3. Fill in `object_id` values

Open `dist/home.nodes.txt` — it lists every mesh node in the GLB. Ceiling
lights typically use the `light_*` prefix:

```
light_living_main_light
light_kitchen_main_light
light_bedroom_master_light
furn_refrigerator_1
furn_sofa_1
Flat_TV_1
...
```

For each HA entity, copy the matching mesh node name into `object_id`.

### 5-4. Visualising fixture positions

While mapping, re-pack with `--show-light-fixtures` to see where each
light sits in the 3D scene:

```bash
floor3d-toolkit pack home.obj -o dist/home_debug.glb --show-light-fixtures
```

Drop in `home_debug.glb` temporarily. When mapping is done, re-pack
without the flag → clean production GLB with invisible fixture boxes.

---

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Red box "Finished with errors" | Open F12 console. Usually `Entity not found` (typo in `entity_id`) or `Cannot read properties of null (reading 'color')` (e.g. `media_player` with bare on/off colorcondition) |
| Only axes show, no model | Remove `camera_position` / `camera_target` from card YAML — let floor3d-card auto-frame |
| Whole scene blown out white | Per-light `lumens` too high. Drop to 500-800. Pair with `globalLightPower: 0.25` |
| Pitch black when lights are off | Re-pack with `floor3d-toolkit pack` — `emissive_factor=0.18` keeps the plan readable at night |
| Adding furniture in SH3D broke existing mappings | Same name → suffix `_1`, `_2`. Use unique names |
| `Tools` menu in SH3D has no export item | Plugin not installed or SH3D wasn't restarted. Check `%APPDATA%\eTeks\SweetHome3D\plugins\` (Windows) or `~/Library/Application Support/eTeks/SweetHome3D/plugins/` (macOS) for the `.sh3p`, then relaunch SH3D |
| 24 entities in card YAML, the whole card breaks | Don't paste them all at once. Wire **1-2 entities → save → confirm → add 5 more**. Incremental wiring keeps the typo blast radius small |

### Mapping best practice — "one change, verify, next"

floor3d-card has many knobs. Tweaking five at once and then debugging is a
losing battle. Recommended loop:

1. Change one thing (e.g. `lumens: 1000`)
2. Save the card + refresh
3. Look — did anything change?
4. If OK, move on. If broken, only that one change needs reverting.

Same goes for entity mapping: ship the card with one entity first, watch it
work, *then* add the rest.

---

## 7. `convert` mode (optional — bypass ExportToHASS)

If you can't or don't want to install the ExportToHASS plugin, or just want
a quick monochrome prototype:

```bash
floor3d-toolkit convert myhome.sh3d --output dist/ --name home
```

Output:
```
dist/
├── home.glb
├── home.entity-mapping.yaml   # auto-generated (overwritten on each run)
└── home.card-config.yaml      # paste into Lovelace
```

Fill mapping with real entity IDs:

```bash
# Copy to a separate user-edited file so re-runs don't clobber your edits
cp dist/home.entity-mapping.yaml dist/home.user-mapping.yaml

# Edit user-mapping.yaml — set each entity_id

# Re-run with --mapping pointing at the user file
floor3d-toolkit convert myhome.sh3d \
  --output dist/ \
  --name home \
  --mapping dist/home.user-mapping.yaml
```

If you accidentally pass the same path as input and output, the toolkit
creates a `.bak` backup before overwriting — but separating files is
safer.

`convert` gives single-colour PBR (no textures). Use `pack` whenever
texture realism matters.

---

## 8. Pairing with redchupa-cards/floor3d-wrapper-card

The `floor3d-wrapper-card` in
[`redchupa-cards`](https://github.com/redchupa/redchupa-cards) layers a
time-of-day rotation UI on top of floor3d-card. Drop in the same
`home.glb` you produced here.

---

## 9. Privacy

The generated `.glb`/`.yaml` files describe your home's geometry. **Never
commit them to a public repository.** This toolkit sends no data
anywhere — all conversion happens locally.
