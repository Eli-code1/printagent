---
name: orienting-for-fdm
description: >-
  Chooses the print orientation of an FDM/FFF part: which way up to lay it on the
  bed to minimize overhangs and support, maximize bed adhesion, keep it short and
  stable, and, when a load direction is given, keep that load along the layers
  rather than across them (the weak direction). Use when deciding how to orient a
  part for printing, reducing supports, improving first-layer adhesion, or trading
  orientation against strength, and as the step between generating a part and
  verifying it. Rests the part on each convex-hull face and scores the candidates;
  composes only trimesh and numpy, with no extra dependencies.
---

# Orienting a part for FDM

This skill decides which way up to print a part. Orientation is upstream of the
manufacturability and structural reviews and of slicing: the overhang gate, the
layer-anisotropy check, and the final slicer transform all assume the part is
already oriented with +Z up. Choose the orientation here first, then hand the
oriented part and its transform downstream.

## How it works
A good resting orientation lays some face of the part's convex hull flat on the bed,
so those hull-face-down orientations are exactly the candidates. Each candidate is
scored, lower is better, on:
- **overhang area**: surface that would overhang past the printer's safe angle and
  need support. This dominates the score.
- **bed-contact area**: a larger flat footprint adheres better and is more stable.
- **height**: shorter parts print faster and topple less.
- **load alignment** (only if a load direction is given): orientations that put the
  load across the layers, the direction prints 40 to 70% as strong, are penalized.

The method is a heuristic, not a slicer. It does not account for the slicer's own
support generation or for cosmetic face preferences, so treat its pick as a strong
default and overrule it when a cosmetic face or a known support trick matters.

## How to run

    python scripts/orient.py PART.stl --max-overhang 45 --out oriented.stl

- `PART.stl` is the part to orient (STL or any mesh trimesh reads).
- `--max-overhang` is the printer's safe overhang angle from vertical (read it from
  the printer profile; 45 is a safe generic default, 60 to 75 on part-cooled machines).
- `--load X,Y,Z` (optional) is the principal load direction in the part's own frame;
  pass it to bias toward printing strong against that load.
- `--out` writes the best-oriented STL, dropped onto z = 0.

It prints JSON: the `best` orientation and the next few `alternatives`, each with the
4x4 `matrix`, the `euler_deg`, the `overhang_area_mm2`, the `bed_contact_mm2`, and the
`height_mm`. Pass `best.matrix` to the downstream steps as the print transform, and
record the `euler_deg` so the choice is legible.

## What to hand downstream
- To `reviewing-manufacturability-fdm` and `reviewing-structural-loads`: the oriented
  STL (or the transform), so their overhang and build-axis checks see the real print pose.
- To `slicing-handoff-bambu`: the transform, as the orientation baked into the handoff.

## Out of scope
- Slicing, support generation, and bed placement of multiple parts: that is the slicer.
- Cosmetic-face or surface-finish optimization: this scores printability, not looks.

## Dependencies
`pip install trimesh numpy`. No other dependencies; it shares the environment with the
other skills.
