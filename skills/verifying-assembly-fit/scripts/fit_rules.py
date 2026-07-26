"""As-printed FDM fit model: how a nominal joint dimension actually leaves the
printer, and whether the resulting fit will assemble by hand in real life.

All values are millimetres and DIAMETRAL (or full-width for slots/rails). The
rationale and sources for every number live in ../references/fit-tolerances.md;
keep the two in sync if you change a value.

Feature kinds: "bore" (internal cylinder), "pin" (external cylinder),
"slot" (internal width), "rail" (external width).

Orientation is relative to the feature's OWN part in its print pose:
  "axial"   - the controlling direction lies in the layer plane (a bore whose
              axis is vertical, a slot between vertical walls): accurate.
  "lateral" - the controlling dimension crosses layers (a horizontal bore's
              vertical diameter, a width measured along Z): sag + quantization.
"""
from __future__ import annotations
import math

# (mu, sigma): systematic error and 1-sigma spread of the as-printed dimension
# relative to the modeled one, for a WELL-CALIBRATED modern CoreXY (X1C/P1S
# class, 0.4 mm nozzle, PLA). "generic" scales these for an untuned machine.
_ERROR_CAL = {
    ("bore", "axial"): (-0.15, 0.05),
    ("bore", "lateral"): (-0.25, 0.08),
    ("pin", "axial"): (+0.05, 0.05),
    ("pin", "lateral"): (+0.10, 0.07),
    ("slot", "axial"): (-0.12, 0.05),
    ("slot", "lateral"): (-0.18, 0.08),
    ("rail", "axial"): (+0.05, 0.05),
    ("rail", "lateral"): (+0.08, 0.07),
}
_GENERIC_MU_SCALE = 1.4
_GENERIC_SIGMA_SCALE = 2.0

SEAM_BULGE = 0.12          # local diameter bump where the perimeter seam lands
ELEPHANT_FOOT = 0.20       # first ~0.5 mm above the bed flares outward this much
ELEPHANT_BAND_MM = 0.6     # feature closer than this to its bed plane is exposed

# intent -> acceptable window of EFFECTIVE diametral clearance (as-printed)
CLASS_WINDOWS = {
    "press": (-0.32, -0.02),     # bites, assembles by hand or light tap
    "snug": (-0.12, +0.20),      # locational: holds by friction, no tools
    "slide": (+0.03, +0.40),     # dovetail / tongue: slides, no slop
    "running": (+0.12, +0.60),   # spins/slides freely forever
}
JAM_BELOW = -0.35              # beyond this PLA cracks or will not seat by hand
BAND_GRACE = 0.08              # tail spill outside the window PASS still tolerates

# A horizontal (lateral) cylinder is anisotropic: a horizontal bore sags
# VERTICALLY while staying near nominal horizontally; a lying pin squishes
# short vertically and fat horizontally. When BOTH sides of a joint are
# lateral, the controlling gap is the per-axis minimum, not a scalar stack.
LATERAL_CYL_AXES = {
    "bore": {"v": -0.25, "h": -0.10},
    "pin": {"v": -0.10, "h": +0.10},
}


def dimension_error(kind: str, orientation: str, layer_height: float,
                    calibration: str = "calibrated"):
    """(mu, sigma) for a feature kind+orientation. Lateral dimensions add layer
    quantization to sigma in quadrature."""
    mu, sigma = _ERROR_CAL[(kind, orientation)]
    if calibration == "generic":
        mu, sigma = mu * _GENERIC_MU_SCALE, sigma * _GENERIC_SIGMA_SCALE
    if orientation == "lateral":
        sigma = math.hypot(sigma, layer_height / 4.0)
    return mu, sigma


def effective_clearance(inner_meas, inner_err, outer_meas, outer_err):
    """(lo, mid, hi) 95%% band of as-printed diametral clearance.
    inner = the enveloping feature (bore/slot), outer = the enveloped (pin/rail)."""
    mu_i, s_i = inner_err
    mu_o, s_o = outer_err
    mid = (inner_meas + mu_i) - (outer_meas + mu_o)
    band = 2.0 * math.hypot(s_i, s_o)
    return mid - band, mid, mid + band


def classify(lo, mid, hi, intent: str):
    """Verdict for a clearance band against an intent class.
    Returns (verdict, advice): verdict PASS | WARN | FAIL.
    PASS = expected value in the window with at most BAND_GRACE of tail spill;
    WARN = expected in the window with bigger spill, or just outside;
    FAIL = expected clearly outside (with a sized dimensional edit)."""
    wlo, whi = CLASS_WINDOWS[intent]
    if mid < JAM_BELOW:
        return "FAIL", (f"expected interference {mid:+.2f} is beyond the "
                        f"hand-assembly limit {JAM_BELOW:+.2f}: parts will jam or "
                        f"crack. Open the bore/slot by {(wlo + whi)/2 - mid:.2f}.")
    if wlo <= mid <= whi and lo >= wlo - BAND_GRACE and hi <= whi + BAND_GRACE:
        return "PASS", ""
    if wlo <= mid <= whi:
        side = "tight" if lo < wlo - BAND_GRACE else "loose"
        return "WARN", (f"expected clearance lands in the '{intent}' window but "
                        f"printer spread [{lo:+.2f}..{hi:+.2f}] spills out the "
                        f"{side} side; fine on a calibrated machine, marginal on "
                        f"an untuned one.")
    if wlo - 0.06 - 1e-9 <= mid <= whi + 0.06 + 1e-9:
        side = "tight" if mid < wlo else "loose"
        return "WARN", (f"expected clearance {mid:+.2f} sits just {side} of the "
                        f"'{intent}' window [{wlo:+.2f}..{whi:+.2f}].")
    delta = (wlo + whi) / 2 - mid
    which = ("open the bore/slot" if delta > 0 else "shrink the pin/rail")
    return "FAIL", (f"expected clearance {mid:+.2f} sits outside the '{intent}' "
                    f"window [{wlo:+.2f}..{whi:+.2f}]: {which} by {abs(delta):.2f}.")
