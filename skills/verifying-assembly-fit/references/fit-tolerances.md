# As-printed FDM fit tolerances: the numbers and why

Authoritative values live in `../scripts/fit_rules.py`; this file records the
reasoning. All numbers are millimetres, diametral (or full width), for a 0.4 mm
nozzle at 0.2 mm layers in PLA. "Calibrated" means a tuned modern CoreXY
(Bambu X1C/P1S class with flow calibration); "generic" scales mu by 1.4 and
sigma by 2 for untuned machines.

## Where the error comes from

**Holes print undersized** (bore axial: mu -0.15). Three stacking effects, all
one-directional: the slicer polygonizes the circle with chords that cut inside
the ideal curve; extruded plastic bulges inward on concave paths (die swell);
and perimeter shrink pulls toward the center. The community rule of thumb of
"drill or model +0.2 on holes" matches this band. Horizontal bores (lateral:
mu -0.25) add gravity sag of bridged top spans and layer quantization of the
vertical diameter, which is why printed horizontal bores read oval.

**Outer surfaces print slightly oversized** (pin axial: mu +0.05). Convex
perimeter bulge is smaller than the concave case. The perimeter seam adds a
local ridge on top (~0.12 diametral at the seam line), which matters for
running and sliding fits that must swallow it every revolution; press fits
just bite harder locally. Lying cylinders (lateral: mu +0.10) gain width from
first-layer squish and lose height to the bed flat.

**Slots shrink, rails grow** for the same reasons as bores and pins; widths
measured across layers (lateral) additionally quantize to the layer height,
hence the sigma term added in quadrature (layer_height / 4).

**Elephant foot**: the first ~0.5 mm above the bed flares outward up to
~0.2 mm on a squished first layer. Any joint feature living in that band
(a rail standing on the bed, a socket opening at the bottom face) sees it
directly, so the checker flags those with "chamfer or de-flare".

## Fit class windows (effective diametral clearance)

| intent  | window          | feel |
|---------|-----------------|------|
| press   | -0.32 .. -0.02  | seats by hand or light tap, holds without glue |
| snug    | -0.12 .. +0.20  | locational; friction holds, fingers remove |
| slide   | +0.03 .. +0.40  | dovetail/tongue glides without slop |
| running | +0.12 .. +0.60  | spins or slides freely, forever |
| (jam)   | below -0.35 expected | PLA cracks or will not seat by hand |

A PASS tolerates up to 0.08 of 95%-band tail outside the window (`BAND_GRACE`):
demanding the whole band inside would make every honest window unreachable,
since the spread of two stacked features is comparable to the window widths.

**Anisotropy of lateral/lateral pairs.** A horizontal bore sags vertically but
holds near nominal horizontally; a lying pin prints short vertically and fat
horizontally. When both sides of a cylinder joint are lateral the checker
evaluates the vertical gap (sagged bore vs squished-short pin) and the
horizontal gap (near-nominal bore vs fattened pin) separately and judges the
smaller one - a scalar worst-vs-worst stack would wrongly combine the bore's
vertical loss with the pin's horizontal gain.

These windows are deliberately wide bands, not machining-grade fits: FDM
repeatability across machines is the dominant term. The band edges come from
the common printed-fit heuristics (0.1-0.2 interference press fits in PLA;
0.3-0.5 clearance for free motion; 0.15-0.25 for snug locating features) that
the community and printed-fit test coupons converge on.

## Why measure-then-model, not model-only

The checker measures the *actual exported mesh* first because modeling errors
(a socket drilled at the wrong depth, a rail wider than its slot) are far
larger than printer tolerances and must not hide under them. The tolerance
model is then applied to the measured value. The report's clearance band is
therefore: (measured geometry) + (expected printing transformation), which is
exactly what lands in your hands.
