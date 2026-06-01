---
name: reviewing-manufacturability-fdm
description: >-
  Runs deterministic design-for-manufacturing (DFM) gates on a 3D part for FDM/FFF
  3D printing — minimum wall thickness, overhang angle, enclosed (un-drained) voids,
  and build-volume fit — then emits a machine-readable verification.json with a
  pass/fail per gate and a nonzero exit code on hard failure. Use when validating,
  checking, or reviewing whether a STEP, STL, or 3MF part is printable / manufacturable
  on an FDM printer, before handing a part to a slicer, or as the verification step of
  an iterative CAD loop. Composes vetted geometry primitives (trimesh, scipy,
  build123d/OCCT); it does NOT invent spatial-measurement code.
---

# Reviewing FDM manufacturability

This skill is the deterministic gate of an agentic FDM design loop. Generation produces
a part; this skill decides whether the part can be printed, and if not, *why*, in a form
the generating step can act on. The principle is strict: **anything computable is computed
here by a vetted script, and the result is ground truth.** Do not re-derive wall thickness,
overhang angle, or void detection in ad-hoc code — call the scripts in `scripts/` and read
their JSON output.

## When to use
- Validating a STEP/STL/3MF part's printability ("is this manufacturable / printable?").
- The verification step inside a generate → check → fix loop.
- Immediately before `slicing-handoff-bambu` hands a part downstream.

## When NOT to use
- Process/printer failures (stringing, layer shift, warping after a real print) → that is
  `analyzing-print-failures`.
- Load-bearing / strength judgement → that is `reviewing-structural-loads`.
- Resin/SLA or CNC rules — these gates encode FDM-specific numbers only.

## Dependencies
`pip install "build123d>=0.10" trimesh scipy numpy`. Optional accelerators: `manifold3d`,
`open3d`, `libigl`. build123d is pre-1.0; **pin the version** — the offscreen/STEP APIs
used here are version-sensitive.

## How to run
Run the orchestrator and read its stdout. Do not reimplement the checks.

    python scripts/run_checks.py PART_FILE \
        --printer bambu_x1c --nozzle 0.4 --layer-height 0.2 --profile structural

- `PART_FILE` may be `.step`/`.stp`, `.stl`, or `.3mf`. STEP gives the most accurate
  results (B-rep available for the experimental offset evidence); STL/3MF are tessellated.
- Exit code is `0` if the part is manufacturable, `1` otherwise — branch on it.
- Full structured result prints to stdout as `verification.json`.

You can also import any single gate:

    from check_min_wall import check_min_wall   # returns a dict

## The gates and how to read them

**watertight** (critical). Reported from mesh health. A non-watertight mesh fails the whole
review — trimesh volume/inertia are meaningless on it, so nothing downstream can be trusted.
Fix the geometry before anything else.

**min_wall** (hard fail). Three methods with deliberately different roles, fused by bias:
- *cone-SDF* is the authoritative pass/fail. From even surface samples it casts a small cone
  of inward rays (a Shape-Diameter-Function sample) and takes the per-point median of the
  surviving ray lengths as the local wall thickness. The cone plus the median reject the
  grazing ray and the concave wraparound that fool a single inward ray, so no corner-exclusion
  heuristics are needed and a solid cube reads its full width. The reported `min_wall_mm` is a
  robust p1, and a part fails when a meaningful fraction of the sampled surface, above a small
  spurious-ray floor, is thinner than T.
- *voxel opening* corroborates only and never decides. It tests whether a ball of radius T/2
  fits everywhere (a morphological opening via a padded distance transform). Because
  `voxelized().fill()` over-thickens thin features by one or two cells, the voxel method
  over-estimates thickness, so its FAIL is strong evidence and its PASS is weak.
- *brep offset* is experimental positive-evidence only (an inward OCCT offset of T/2). Success
  is weak evidence that walls are at least T; failure is inconclusive and is never a fail.
- Verdict rule (bias-aware): a cone-SDF FAIL is a FAIL, with high confidence when the voxel
  opening also fails. A cone-SDF PASS is a PASS unless the voxel opening fails while the cone
  reading sits near the threshold, in which case the gate returns INDETERMINATE rather than a
  silent pass. The verdict uses the shared vocabulary PASS, FAIL, INDETERMINATE, or NOT_RUN,
  and the result also carries an `epistemic_weight` and a `plain_consequence` string.

**overhangs** (warning, not hard fail). Measures each downward-facing surface's angle from
vertical and flags area steeper than the printer's safe threshold (45° generic, 60–75° on
modern part-cooled machines, read from the profile). Overhangs are *supportable*, so this is
a warning — but it is the agent's strongest pre-print lever. Resolve by reorienting the build
direction or converting downward-facing fillets to 45° chamfers, not by adding support blindly.

**enclosed_volumes** (hard fail). Flood-fills empty space from the bounding box; any empty
region unreachable from outside is a sealed cavity that traps support/moisture and cannot
drain. The cleanest single signal in the whole table. Fix by adding a ≥3 mm vent hole. Note
the `pitch_mm` — a legitimate drain smaller than the voxel pitch can be falsely sealed.

**build_volume** (hard fail). Compares the part's footprint and height against the printer's
*usable* envelope (nominal bed minus a few mm for purge/clamps) in the current build
orientation (Z up). Reports an oriented-bounding-box hint: if `obb` fits but the part as
oriented does not, reorienting may rescue it.

## What to do on each failure (loop contract)
Hand these back to `generating-build123d` as concrete edits:
- min_wall fail → thicken the offending shell to ≥ T, or add ribs/gussets, or (if cosmetic)
  accept and switch profile.
- overhang warning beyond the printer limit → reorient the build direction, or chamfer the
  downward edges; only then fall back to support.
- enclosed void → add a vent hole (≥ 3 mm) at the reported centroid.
- build_volume fail → split the part, scale down, or reorient (use the OBB hint).

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

## Caveats
- **Orientation matters.** Overhang and build-volume gates assume the part is already
  oriented for printing with +Z up. Orientation selection is upstream of this skill.
- **Voxel pitch vs memory.** Min-wall and void detection voxelize; on large parts pitch is
  auto-coarsened to stay within a voxel budget, which lowers confidence. The `note` and
  `confidence` fields say when this happened.
- **Thresholds are derived, not fixed.** All numbers scale from nozzle line-width and layer
  height (see `references/fdm-rules.md` for the full rule set, rationale, and sources). The
  scripts read defaults from `fdm_rules.py`.
