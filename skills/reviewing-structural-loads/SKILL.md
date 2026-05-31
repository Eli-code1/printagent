---
name: reviewing-structural-loads
description: >-
  Reviews whether an FDM 3D-printed part will survive its intended load: checks the principal
  load direction against the layer plane (the anisotropy that makes Z 40-70% as strong),
  finds the weakest cross-section along the build axis, flags sharp concave edges that act as
  stress risers, and reports mass, center of mass, and inertia. Use when assessing strength,
  stiffness, whether a part will hold / break / snap under load, durability, or orientation
  for strength. Produces a structured structural_review.json; advisory, not a hard gate.
---

# Reviewing structural loads

This is the second reviewer of the design loop's expert panel, and it judges what the
geometric gate cannot: will the part hold under its load. Most of its output is computed
(mass properties, cross-sections, stress-riser geometry), with the load-direction judgment
resting on the principal load supplied in the part spec.

## When to use
- After a part passes `reviewing-manufacturability-fdm`, to judge in-use strength.
- When the user asks whether a part is strong/stiff enough or will break.
- To decide or validate print orientation for strength.

## What it checks
- **Layer anisotropy** (the headline). FDM parts are 40-70% as strong across layer lines (Z)
  as in-plane. The check projects the principal load onto the build axis: if a large fraction
  of the load is carried across layers, it warns and suggests reorienting so the load sits in
  XY. This is the single most consequential structural decision for a printed part.
- **Weakest cross-section.** Slices the part along Z and reports the smallest cross-sectional
  area and its height — the plane where layer adhesion carries the least material and where a
  part loaded in Z-tension tends to fail. A sharp local dip is a neck to thicken or fillet.
- **Stress risers.** Finds sharp concave (reentrant) edges from face adjacency and recommends a
  fillet, since sharp internal corners concentrate stress and seed cracks.
- **Mass properties.** Volume, estimated mass at a material density, center of mass, principal
  inertia, and oriented-bounding-box slenderness.

## How to run
    python scripts/run_structural.py PART_FILE \
        --load-dir 0 0 1 --material PLA --infill 0.25

`--load-dir` is the principal load vector (any scale). `--material` keys the density table in
`references/materials.md`. Output prints as `structural_review.json` with metrics, warnings,
and a one-line verdict.

## How the panel should use it
Treat warnings as inputs to the orchestrator, not as a build-blocking gate. A
"load aligned with weak axis" warning typically routes back to `generating-build123d` as a
*reorientation* request (which then re-runs the manufacturability gate, since orientation
changes the overhang and build-volume results). A sharp-neck or stress-riser warning routes
back as a thicken/fillet edit.

## Caveats
- **Mass is an estimate.** Printed parts are not solid; reported mass is solid mass at the
  material density. Actual mass falls between walls-only and solid depending on infill — the
  script reports a rough infill-scaled figure, not an FEA result.
- This skill does not run finite-element analysis; it computes geometric proxies for strength.
  For load-critical parts, treat its output as a screen, not a certification.
- Like the gate, it assumes the part is oriented with +Z up.
