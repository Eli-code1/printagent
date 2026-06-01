# Part templates

Known-good, parametric starting points for the highest-volume FDM part families. Each
template is a Python module exposing `build(spec) -> Part` (and `build_lid(spec)` for a
two-part design) that composes the vetted helpers in `../scripts/dfm_helpers.py`, paired with
a JSON metadata sidecar. Every template here is proven to pass the manufacturability gate by
`test_templates.py`.

## The contract
- `build(spec: dict | None) -> Part` returns one printable build123d Part, oriented base on the bed.
- `spec` overrides the module's `DEFAULTS`; omit it to take the defaults.
- A two-part design also exposes `build_lid(spec)`.

## The metadata sidecar (`<id>.json`)
- `id`, `family`, and `intent`: identity and a one-line description.
- `keywords`: the terms the plain-language router matches a request against.
- `parameters`: each with a default, units, and a description (what the router asks the user for).
- `invariants`: the expected `solid_count`, `watertight`, `planar_bottom`, and the rest, fed to
  `../scripts/run_invariants.py` as the cheap pre-gate.

## How they are used
1. The `designing-in-plain-language` router matches a request's words against `keywords`, and on
   a confident match it proposes the template and asks only for the parameters it needs.
2. `build(spec)` produces the part from the collected parameters.
3. `../scripts/run_invariants.py` checks the built part against the sidecar `invariants` cheaply,
   then `reviewing-manufacturability-fdm` runs the full gate.

## Current templates
All nine families the plain-language router can propose now have a module here.
- `bracket`: a wall-mount L bracket, gusseted, with holes in both legs.
- `holder`: an open-top holder or organizer.
- `box_with_lid`: a two-part box with a friction-fit lid.
- `hook`: a wall hook with a screw-through back plate.
- `adapter`: a tubular sleeve or coupler with a through bore.
- `mounting_plate`: a flat plate with a grid of screw holes.
- `tray`: a shallow open-top tray with optional dividers.
- `stand`: an angled stand for a phone, tablet, or sign.
- `plaque`: a flat plaque with a raised border and a hang hole.

## Adding a template
Write `<id>.py` with a `build(spec)` that composes the helpers, add `<id>.json`, then run
`python test_templates.py`. A template is not done until it passes the gate in that harness.
