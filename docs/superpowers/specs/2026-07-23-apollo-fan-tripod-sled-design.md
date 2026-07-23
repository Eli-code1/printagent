# Apollo Fan tripod sled — design spec

Date: 2026-07-23. Status: approved in conversation (photos + caliper measurements + interactive
3D model reviewed by Eli). Phase 1 scope: slot-fit test coupon only.

## Goal

Let the "inbio Apollo Fan" (a ~110 x 63.5 x 119 mm rounded-cube 12V desk fan, promo unit
styled after InBio's Apollo air sampler; no OEM mount exists) attach to any camera tripod.
A printed sled engages the two tapered slots molded into the fan's base and carries a
1/4-20 tripod socket underneath. Use case is upright, aimed forward; light retention is
enough (gravity holds the fan down, ribs stop sliding and rotation).

## Device map (measured, feet removed)

All from Eli's calipers and photos; the fan sits on the plane of the label platform and
foot recesses, which are co-planar ("base plane"). Front = grille face.

- Base footprint: 110.5 wide x 63.5 deep mm (4.35 x 2.5 in); height ~119 mm (4.7 in).
- DC jack: centered on the BACK face, low. No power switch anywhere on the base.
- Two OUTER tapered slots ("the connector"), one per side, running front-to-back:
  - Closest slot edge ~30 mm from each side edge; centerlines ~±23 mm from the fan
    centerline (~46 mm center-to-center, Eli's "1.8 in").
  - Slot front end 10.15 mm from the front edge; length ~43-44 mm; back tip lands
    ~10.3 mm from the back edge (near-symmetric, cross-checked and confirmed by Eli).
  - Kite (lens) plan profile: ~4.0 mm wide at the front end (ASSUMED, not yet measured),
    widening to the peak 4.60 mm at ~19 mm from the slot front, back to ~4.0 mm at
    ~27 mm, then a long taper to 1.35 mm at the back tip.
  - Depth 2.75 mm below the base plane.
- Two INNER channels flanking the raised label platform (~41 mm long), each with an
  assembly screw recessed ~20 mm from the front edge (43 mm from the back). Screws sit
  below the base plane; a flat plate bridges them without contact. Do not use these
  screws for mounting (Eli's requirement).

## Full sled design (phase 2)

- Flat plate ~56 x 44 x 3 mm, top face against the base plane, centered between slots.
- Two kite ribs on top matching the slots' wide front portion: length ~30 mm from the
  slot front end, width stations (front, 19 mm, 27 mm, end): 3.4 / 4.0 / 3.4 / 2.9 mm
  (nominal ~0.3 mm per-side clearance), height 2.0 mm (0.75 mm shy of slot floor).
  The bulge keys into the slot's 4.6 mm peak, resisting fore-aft creep; drop-in from
  above, not slide-in (the slot is a closed pocket; bulge > front-end width).
- 1/4-20 printed-thread socket, modeled thread, in a stubby boss directly under the
  plate (~7 mm tall, ~16 mm dia), chamfered mouth, >=5 turns engagement. Boss center
  under the fan's balance point: on the fan centerline, ~32 mm from the front edge.
  Total stack under the fan ~10 mm ("snug, not way below" — Eli).
- Material PETG (default profile also fine in PLA for fit checks). Print plate-down.

## Phase 1: fit-check coupon (this build)

Purpose: verify the connector geometry only — do the ribs drop into the slots, seat
flat, and hold against slide/rotation with acceptable snugness?

- The plate and both ribs exactly as specified above, NO tripod boss (faster print,
  nothing else to confound the fit reading).
- A small front-edge chamfer/label notch to mark FRONT so the coupon goes in the right
  way round.
- Parametric build123d Python (single PARAMS dict at top: all slot stations, spacing,
  clearance, heights); exports STEP (Onshape import) + STL (print). Clearance is one
  number; re-print variants by changing it alone.
- Runs the Printagent loop: invariants pre-gate, then the DFM gates
  (min-wall, overhang, enclosed voids, build volume) with print orientation chosen by
  orienting-for-fdm conventions (+Z up, plate on bed).

## Acceptance (phase 1)

- Gates pass; STEP and STL produced under parts/apollo-fan-tripod-sled/.
- Physical: coupon drops into both slots simultaneously, sits flush on the base plane,
  no rock; resists lateral slide and yaw by hand; removable without tools. Snug/loose
  feedback maps to the single clearance parameter.

## Open items

- Slot width at its very front end is assumed 4.0 mm — measure when convenient; only
  the rib's front station changes.
- Exact jack height on the back face (cosmetic for the model; irrelevant to the sled).
- Phase 2 adds the threaded boss and (if fit demands) root fillets sized under the
  per-side clearance so they cannot hold the plate off the base plane.
