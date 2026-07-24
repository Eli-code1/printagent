# Apollo fan tripod sled

Spec: `docs/superpowers/specs/2026-07-23-apollo-fan-tripod-sled-design.md`.
Two parts live here: the phase-1 fit-check coupon (converged over four prints) and
the phase-2 sled built on that converged fit.

## Phase-2 sled

Plate + the two kite ribs (geometry imported from `coupon.py` v6 unchanged: gap
datum 40.2, clearance 0.15/side, 22 mm ribs) + a 16 mm boss underneath with a
modeled 1/4-20 printed thread (5.2 turns, blind, chamfered mouth) centered under
the fan's balance point.

### Files
- `sled.py` — parametric build123d source (edit `PARAMS`; rib fit comes from `coupon.py`)
- `sled.step` — import this into Onshape (lossless B-rep, named `apollo_sled`)
- `sled.fs` — Onshape-native parametric twin: paste into a Feature Studio, then add
  the "Apollo sled" custom feature to a Part Studio for a dialog with every
  dimension editable live. For visual design iteration; `sled.py` stays the
  source of truth for printing (it carries the modeled thread).
- `sled.stl` — slice this
- `sled_spec.json` — invariants for the pre-gate
- `renders/sled_*.png` — previews

### Print (sled)
- Material: PETG; 0.2 mm layers, 0.4 mm nozzle; walls >= 3
- Orientation: as exported — boss on the bed, ribs up. This keeps the rib fit
  surfaces and the fan-contact face pristine and the thread axis vertical.
- **Supports: required** under the plate (7 mm table-top over the boss); tree
  supports, touching buildplate only. The underside is non-cosmetic.
- Gate verdicts: watertight, voids, build volume PASS; overhangs WARNING is the
  supported plate underside (by design); min_wall INDETERMINATE is the same
  chamfer-feather-edge signature the four-times-printed coupon shows (authoritative
  cone-SDF min 2.36 mm vs 1.6 mm threshold) — reviewed, benign.
- Thread fit knob: `thread_fit` in `sled.py` (default +0.30 mm diametral). Screw
  binds: raise by 0.10. Screw sloppy: lower by 0.10. Rebuild:
  `../../.venv/bin/python ../../skills/generating-build123d/scripts/build_and_check.py sled.py --printer bambu_x1c --profile structural --gate-dir ../../skills/reviewing-manufacturability-fdm/scripts --stem sled`

## Phase-1 fit-check coupon

Tests whether the two kite ribs replicate the fan's base-slot connector. No tripod
boss.

### Files
- `coupon.py` — parametric build123d source (edit `PARAMS`, rerun to regenerate)
- `coupon.step` — import this into Onshape (lossless B-rep)
- `coupon.stl` — slice this
- `coupon_spec.json` — invariants for the pre-gate
- `render.py`, `renders/` — previews (`python render.py sled` renders the sled)

### Print (coupon)
- Material: PETG or PLA (fit test only; PETG matches the final sled)
- Layers: 0.2 mm, 0.4 mm nozzle; walls >= 3; infill anything
- Orientation: as exported — plate on the bed, ribs up. No supports, no brim needed
- Verified: all five DFM gates pass (watertight, min wall, overhangs, voids, volume)

### Fit test
1. Feet off the fan; set it upside down.
2. The notched edge of the coupon faces the FRONT (grille side).
3. Lower straight in — both ribs into the outer black slots. It should drop in,
   sit flush on the base plane with no rock, and resist sliding/twisting by hand.

Report one of: drops-in-snug (perfect), needs-press (tight), rattles (loose),
won't-seat (interference — note where it hangs up).

### Tune
One knob: `clearance_side` in `PARAMS` (0.15 mm per side as of v6).
- Too tight / won't seat: raise it by 0.10 -> 0.40
- Rattles / slides: lower it by 0.10 -> 0.20
Rebuild: `../../.venv/bin/python ../../skills/generating-build123d/scripts/build_and_check.py coupon.py --printer bambu_x1c --profile structural --gate-dir ../../skills/reviewing-manufacturability-fdm/scripts --stem coupon`
