---
name: generating-build123d
description: >-
  Authors and edits parametric 3D parts as build123d (Python/OCCT) code for FDM 3D
  printing, exports STEP and STL, runs the manufacturability gate, and translates each
  gate failure into a concrete code edit. Use when generating, modeling, designing, or
  fixing a printable CAD part from a description, when writing build123d or CadQuery-style
  CAD code, or as the generate/fix half of an iterative design loop. Composes vetted,
  DFM-correct part helpers and known-good build123d idioms rather than free-handing geometry.
---

# Generating parts with build123d

This skill is the generate/fix half of an agentic FDM design loop. It produces a part as
build123d code, exports it, and pairs with `reviewing-manufacturability-fdm` to verify it.
The discipline mirrors that skill's: **compose vetted primitives, do not free-hand geometry
the kernel will choke on.** Use the helpers in `scripts/dfm_helpers.py` and the idioms in
`references/build123d-idioms.md`; they bake the DFM numbers in so generated geometry tends to
pass the gate on the first or second pass.

## Step 0, clarify before you draw (bounded)
Text specs are systematically under-specified. Before writing any geometry, fill the spec in
`scripts/spec_schema.py` and ask the user only the load-bearing unknowns you cannot infer:
- what the part *does* (its function and any mating part it joins),
- the few driving dimensions and the envelope it must fit,
- fits/clearances to mating parts (sliding, press, fastened, print-in-place),
- the principal load and its direction (drives print orientation),
- target printer/material (drives the gate's thresholds).

Ask at most one bounded round. For anything still missing, choose a sensible default, **state
the assumption inline**, and proceed, do not stall the loop on clarification.

## Authoring rules
- **Prefer algebra mode.** `part = Box(40, 20, 10); part -= Pos(0, 0, 5) * Cylinder(2, 10)`.
  It is stateless, easy to chain, inline-test, and refactor, the lowest-error path for
  generated code. Builder mode (`with BuildPart() as bp: ...`) is fine when a feature genuinely
  needs the context, but do not mix paradigms in one part.
- **Use typed selectors, never strings.** `part.edges().filter_by(GeomType.CIRCLE).sort_by(SortBy.RADIUS)[-1]`,
  not a string DSL. Every token is a plain Python identifier.
- **Never mix import styles.** Pick `from build123d import *` *or* `import build123d as bd`
  for the whole part. Pin the build123d version, the export/import APIs are version-sensitive.
- **Compose the helpers.** `heatset_boss`, `clearance_hole`, `shell`, `chamfer_bottom_edges`,
  `add_vent`, `mouse_ears`, and the fastener and feature set (`counterbore_hole`,
  `countersink_hole`, `tap_hole`, `captive_nut_pocket`, `add_standoff`, `add_rib`,
  `add_gusset`, `slot_hole`) in `dfm_helpers.py` already encode the rule numbers. Reach for
  them before hand-modelling a boss, hole, shell, recess, rib, or vent.
- **Defer fillets and chamfers to the end** of the build, they are the most kernel-fragile op
  and applying them last avoids invalidating earlier selections.

## When the kernel fails
OCCT throws on a predictable set of operations. The playbook is in
`references/kernel-failures.md`; the short version: a fillet/chamfer that blows up means the
radius is too large for an adjacent feature (reduce it, or defer it); a loft/sweep failure
usually means non-tangent rails (substitute or simplify); a boolean that returns an empty or
invalid result usually means coincident faces (nudge one body by a small epsilon).

## Choose orientation before checking
The gate's overhang and build-volume checks assume the part is oriented for printing with **+Z
up**. Decide orientation deliberately first, put the principal tensile load in the XY plane
(layer-line anisotropy makes Z 40-70% as strong), minimise overhang area and support, and keep
the footprint stable, then export in that orientation.

## Export and check (the loop)
Export STEP (lossless, gives the gate a B-rep) and STL, then run the loop glue.
STEP product names come from build123d `label`s, and downstream CAD (Onshape, Fusion,
FreeCAD) shows them as the part names on import, so set `part.label` (and a label per
compound child on multi-body parts) to real names; `export_part` falls back to the file
stem and `<stem>_1..n` for anything left unlabeled. Identical bodies dedupe to one STEP
product, so give copies of the same part one shared name.

    python scripts/build_and_check.py my_part.py \
        --printer bambu_x1c --profile structural \
        --gate-dir ../reviewing-manufacturability-fdm/scripts

`my_part.py` must define a module-level `part` (a build123d object) or a `build()` returning one.
The script exports the part, invokes the gate, and prints a combined result whose `fix_list`
names the exact edit for each failure. Iterate on `fix_list` until `manufacturable` is true,
applying the report's stop conditions: stop when converged, when K iterations pass with no
improvement, or when the budget is spent, then escalate to a human.

## Cheap invariant pre-gate (run before the expensive gate)
Fill the `Invariants` block of the `PartSpec` (expected bounding box, volume with a tolerance,
solid count, through-hole count, watertightness, and a planar bottom), then check the built
part against it first:

    python scripts/run_invariants.py my_part.stl spec.json

It runs in a few milliseconds and returns a `fix_list`. Send only candidates that pass on to
the expensive `reviewing-manufacturability-fdm` gate; this filters out obviously-wrong
generations (wrong size, missing or extra bodies, wrong hole count) before any heavy compute.

## Loop control and stop conditions
The outer regenerate-and-reverify loop MUST terminate. Evaluate these conditions after each
verification and act on the first that applies:
1. **Convergence.** When all invariants pass and the verification `overall_verdict` is `PASS`,
   STOP; the part is done.
2. **Max iterations.** STOP after at most 5 outer regenerate-and-reverify iterations.
3. **No improvement (stuck).** Hash the sorted set of failing gate names each iteration; if it
   is identical to the previous iteration, the loop is stuck, so STOP and escalate instead of
   trying another fix.
4. **Regression.** If the number of failures grows after an edit, that edit made things worse;
   revert to the previous version and escalate.

To escalate, state to the user the specific decision that is needed, then stop making changes
and wait for their input. There is no paused-loop primitive, so escalation is just a clear
hand-back.

## Failure → edit
- `min_wall` → `shell(part, t)` with a larger `t`, add ribs/gussets, or thicken the named region;
  thin-region coordinates are in the gate's `thin_locations_mm`.
- `overhangs` beyond the printer limit → reorient the build, or `chamfer_bottom_edges(part)` /
  convert downward-facing fillets to chamfers.
- `enclosed_volumes` → `add_vent(part, centroid, 3.0)` at the reported void centroid.
- `build_volume` → split the part, scale down, or reorient (use the gate's `reorient_could_help`).
- `watertight` false → ensure the result is a single closed solid; a stray boolean leaving a
  sliver or coincident face is the usual cause.

## Dependencies
`pip install "build123d>=0.10" trimesh scipy numpy`. Shares its environment with
`reviewing-manufacturability-fdm`.
