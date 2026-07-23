# Apollo fan tripod sled — phase-1 fit-check coupon

Tests whether the two kite ribs replicate the fan's base-slot connector. No tripod
boss yet. Spec: `docs/superpowers/specs/2026-07-23-apollo-fan-tripod-sled-design.md`.

## Files
- `coupon.py` — parametric build123d source (edit `PARAMS`, rerun to regenerate)
- `coupon.step` — import this into Onshape (lossless B-rep)
- `coupon.stl` — slice this
- `coupon_spec.json` — invariants for the pre-gate
- `render.py`, `renders/` — previews

## Print
- Material: PETG or PLA (fit test only; PETG matches the final sled)
- Layers: 0.2 mm, 0.4 mm nozzle; walls >= 3; infill anything
- Orientation: as exported — plate on the bed, ribs up. No supports, no brim needed
- Verified: all five DFM gates pass (watertight, min wall, overhangs, voids, volume)

## Fit test
1. Feet off the fan; set it upside down.
2. The notched edge of the coupon faces the FRONT (grille side).
3. Lower straight in — both ribs into the outer black slots. It should drop in,
   sit flush on the base plane with no rock, and resist sliding/twisting by hand.

Report one of: drops-in-snug (perfect), needs-press (tight), rattles (loose),
won't-seat (interference — note where it hangs up).

## Tune
One knob: `clearance_side` in `PARAMS` (default 0.30 mm per side).
- Too tight / won't seat: raise it by 0.10 -> 0.40
- Rattles / slides: lower it by 0.10 -> 0.20
Rebuild: `../../.venv/bin/python ../../skills/generating-build123d/scripts/build_and_check.py coupon.py --printer bambu_x1c --profile structural --gate-dir ../../skills/reviewing-manufacturability-fdm/scripts --stem coupon`

---

# Full sled (phase 2): sled.py / sled.step / sled.stl

Uniform 56 x 38 x 10 mm slab; calibrated ribs (gap 40.3, clearance 0.15) on top,
blind printed 1/4-20 socket (major 6.5, 5.5 turns) underneath at the balance
point. Prints as exported, plate down, NO supports (the socket's flat ceiling is
a 6.5 mm bridge; any slicer handles it). PETG, 0.2 mm layers, 4+ walls.
The gate passes; the overhang warning is the internal thread itself, which is
normal and printable. First time in: run the tripod screw in once to shave the
thread crests; it cuts smoother every turn after.
