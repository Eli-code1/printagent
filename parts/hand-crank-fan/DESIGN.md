# Hand-crank desk fan — design

Date: 2026-05-31
Status: BUILT + verified manufacturable (one piece, print-in-place). See PRINT.md to print.
Workspace: `parts/hand-crank-fan/`

## In plain words

A palm-sized desk gadget. You put a finger on a grip knob and spin a **big wheel**;
teeth around its rim drive a **small gear** beside it; the small gear spins about
**4x faster** than your hand and carries the **fan blades**, so a lazy crank turns
into a satisfying blur. It prints as **one piece** that works straight off the bed —
no assembly, no supports — and rests leaning gently back toward you like a desk clock.

The breeze is a gentle puff, not real cooling. That is intentional: the goal the user
chose is a fun, satisfying gadget, with airflow as a bonus.

## Decisions (from brainstorming)

| Choice | Decision |
|--------|----------|
| Purpose | Fun desk gadget — satisfying spin + visible whir; breeze optional |
| Mechanism | Single-stage spur-gear step-up, parallel axes in one plane |
| Assembly | Snap-together: 5 parts on one plate, press-in pins (revised from print-in-place; see Revisions) |
| Size | Palm-sized, ~110 mm overall width |
| Resting pose | Leans back ~20° toward the user (desk-clock style) |
| Printer | Bambu Lab X1C, bed 256 x 256 x 256 mm |
| Material | PLA |

## Engineering targets (starting numbers; the gate + fix loop refine these)

Spur gears, 20° pressure angle, module **m = 1.5 mm** (chunky teeth for FDM strength):

- **Wheel (input):** z1 = 48 teeth -> pitch dia 72 mm. Carries a finger grip knob near the rim.
- **Pinion (fan):** z2 = 12 teeth -> pitch dia 18 mm. Carries the fan rotor.
- **Step-up ratio:** 48 / 12 = **4.0x**.
- **Center distance:** m*(z1+z2)/2 = **45 mm**.
- **Overall width:** wheel R (36) + center distance (45) + pinion R (9) ~= 90 mm of mechanism,
  plus base margins -> ~105-115 mm. Target ~110 mm.
- **Gear face (print height of the gears):** ~8 mm.

Pins and clearances (print-in-place):

- **Pins:** vertical posts ~5 mm dia, integral to the base.
- **Bore clearance:** ~0.45 mm radial gap (known-good free-spin gap on the X1C for PLA).
- **Pin cap / retention:** a small lip or printed washer-cap so the gears do not lift off.

Fan rotor (the part that must clear everything):

- Mounted on a hub that **elevates the blades above the wheel's top surface** so the blade
  disc sweeps freely over the wheel (the pinion sits only ~9 mm from the wheel rim, so blades
  cannot share the wheel's plane).
- 4 blades, tip radius ~26-30 mm, **modest helical pitch** so the blades print without support
  and push a little air.

Grip knob:

- Rounded post on the wheel, ~6 mm dia, ~12 mm tall, offset near the rim for finger spinning.

Pose / print orientation:

- Display tilt ~20° back toward the user. Realized by printing on a shallow wedge facet so the
  mechanism plane sits ~20° off the bed; this keeps every print-in-place overhang gentle
  (<= ~45° from vertical) and support-free, while letting the finished part lean back on its base.

## What "done" means

1. `generating-build123d` produces the part as parametric code and exports STEP + STL.
2. `reviewing-manufacturability-fdm` gate passes for walls, overhangs, drainage, and build-volume
   fit — OR each failure is understood and either fixed or judged a false positive of the
   print-in-place gap (hand-verified; see note below).
3. `reviewing-structural-loads` is sane for a light-use desk gadget (advisory).
4. The free-spinning gaps and the gear mesh are hand-checked, because the min-wall gate is known
   to misread print-in-place gaps (rays cross the spin clearance).
5. `slicing-handoff-bambu` packages a millimetre 3MF + STEP + manifest for the X1C.

## Known risk

Single moving piece -> the spin clearances and gear teeth must print cleanly. Mitigations:
generous 0.4 mm gaps, chunky module-1.5 teeth, gentle tilt to keep overhangs printable, and a
manual review of the moving gaps rather than trusting the automated min-wall gate alone.

## Revisions during build (as-built)

- **Gear teeth thinned to 30% of pitch (`tooth_frac=0.30`).** The first cut had teeth so fat
  their flanks interfered at mesh: `check_spin.py` found the wheel and pinion overlapping by
  -0.30 mm at the printed angle — they would have printed FUSED and never turned. Thinning the
  teeth opened a ~0.36 mm backlash gap (~one nozzle width); spin is now verified free and driving.
- **Base lightened from a 197 cc solid wedge to a ~72 cc ribbed shell** (2.0-2.4 mm walls/ribs,
  hollow, open bottom) so it does not print as a solid brick. The deck roof bridges each cell.
- **Spin verified geometrically** (`check_spin.py`): printed-angle gaps base<->rotor 0.40 mm,
  wheel<->pinion 0.36 mm; mesh tip-root clearance +0.375 mm; no jam over a full tooth cycle.
- **min_wall disposition:** min_wall hard-fail is a false positive (grazing rays on sharp tooth
  tips / ribbed-base corners). True per-part min wall (p1) >= ~1.0 mm everywhere. See
  `verification.json`.
- **Switched from print-in-place to SNAP-TOGETHER (5 parts)** at the user's request, because
  print-in-place inherently triggers the slicer's "floating regions" warning (separate parts on
  spin gaps). Now: base + wheel + fan-pinion + two press-in pins. Each gear has a D5.5 bore that
  spins on a D5.1 pin shaft (0.40 mm clearance); the pin's lower section press-fits the base
  (D5.0 hole, 0.10 mm interference); the D6.6 head keeps the gear captive (the pinion hub is
  counterbored so its head seats on a shoulder). Parts print flat on one plate -> no floating
  islands, crisp gears. Verified in `check_spin.py`.
