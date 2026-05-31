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

**min_wall** (hard fail). Three methods with deliberately different roles:
- *ray thickness* — the authoritative pass/fail. From even surface samples it casts a ray
  inward along the −normal to the opposite wall; that distance is the local wall thickness.
  Unlike a max-inscribed-sphere it does **not** collapse at convex edges (a solid cube reads
  its full width everywhere), so no corner-exclusion heuristics are needed. The reported
  `min_wall_mm` is a robust p1 of those samples, and `thin_locations_mm` points at the thin
  regions. Fails when a meaningful fraction of the sampled surface — above a small
  spurious-ray floor — is thinner than T.
- *voxel opening* — CORROBORATING only, never the verdict. Tests whether a ball of radius T/2
  fits everywhere (morphological opening via a padded distance transform). trimesh's
  `voxelized().fill()` over-thickens thin features by ~1–2 cells, so on its own it can miss a
  genuinely thin wall — it is reported but does not decide.
- *brep offset* — EXPERIMENTAL positive-evidence only (inward offset of T/2). OCCT offset is
  fragile; success is weak evidence walls ≥ T, failure is **inconclusive and never a fail**.
- Verdict rule: fail if ray thickness finds a sub-T region above the noise floor; pass if not;
  `null` (inconclusive) only if sampling/ray-casting could not run. `confidence` is `high`
  whenever rays ran; the voxel method still notes `low` confidence on large parts where its
  pitch was coarsened.

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

## Caveats
- **Orientation matters.** Overhang and build-volume gates assume the part is already
  oriented for printing with +Z up. Orientation selection is upstream of this skill.
- **Voxel pitch vs memory.** Min-wall and void detection voxelize; on large parts pitch is
  auto-coarsened to stay within a voxel budget, which lowers confidence. The `note` and
  `confidence` fields say when this happened.
- **Thresholds are derived, not fixed.** All numbers scale from nozzle line-width and layer
  height (see `references/fdm-rules.md` for the full rule set, rationale, and sources). The
  scripts read defaults from `fdm_rules.py`.
