# Test fixtures

All fixtures here MUST be **synthetic** — pure inventions, no real homes.
See [`PLAN.md` §7](../../PLAN.md) for the security rationale.

## Files

| File | Description | How to (re)generate |
|---|---|---|
| `sample_apartment.sh3d` | Generic 2-bedroom 30평형 apartment, no personal data | Sweet Home 3D GUI, see below |
| `sample_apartment.expected.json` | Expected parser output | Will be checked in after M1 lands |

## Generating `sample_apartment.sh3d` (manual, one-time)

`.sh3d` files are produced by the [Sweet Home 3D](https://www.sweethome3d.com/) desktop
application. The fixture should be a small, generic floor plan:

1. Launch Sweet Home 3D (free / GPL).
2. Draw two rectangular bedrooms, one bathroom, one kitchen, one living/dining room.
3. Use the bundled stock furniture catalog only — **do not import any catalog with
   personally identifying model names**.
4. Add at least:
   - 1 ceiling light per room (point light)
   - 1 generic "TV" placeholder in the living room
   - 1 generic "Refrigerator" in the kitchen
5. Save as `sample_apartment.sh3d` in this directory.

### Do NOT include

- Your real apartment layout, room sizes, or balcony shape.
- Real product brand names in furniture names.
- Custom textures derived from photos of your home.
- Room labels (in any language) that match your actual home's layout.

The `.gitignore` allows `sample_*.sh3d`, `sample_*.obj`, etc. — make sure your
filenames stick to the `sample_` prefix.
