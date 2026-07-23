"""Full tripod sled for the inbio Apollo Fan (phase 2).

A uniform 10 mm slab: fan-facing top carries the two calibrated kite ribs
(fit-check coupon prints #1-#4 dialed the numbers), the underside carries a
blind printed 1/4-20 socket under the fan's balance point. Uniform thickness
instead of the spec's plate+boss so the part prints plate-down with ZERO
supports; total stack under the fan stays the approved ~10 mm.

Frame: +Z up in print orientation (bed at z=0; fan sits on z=10, ribs to z=12).
+Y = fan front (grille). Origin XY = fan centerline at half the box depth,
which puts the thread under the balance point. Box front edge lands at
y=+31.75; the slots start 10.15 behind it (y=+21.6).

Thread: 1/4-20 UNC is a 60-degree form, so IsoThread with major=6.5 (0.15
printed-fit allowance over the nominal 6.35) and pitch=1.27 mates a standard
tripod screw. ~5.5 turns of engagement.

Spec: docs/superpowers/specs/2026-07-23-apollo-fan-tripod-sled-design.md
Calibration artifact: coupon.py (same slot model and fit numbers).
"""
from __future__ import annotations
from build123d import (Align, Axis, Box, Cone, Cylinder, GeomType, Polygon,
                       Pos, chamfer, extrude)
from bd_warehouse.thread import IsoThread

_CCM = (Align.CENTER, Align.CENTER, Align.MIN)

PARAMS = dict(
    # measured slot geometry (per side, mm) — calibrated via the fit coupon
    slot_front_w=4.0,          # width at the slot's front end (ASSUMED, unmeasured)
    slot_peak_d=8.85,          # peak distance from the slot's front end
    slot_peak_w=4.65,          # the kite's widest point (4.6-4.7 measured)
    slot_taper_slope=0.10,     # mm of width lost per mm behind the peak
    slot_depth=2.75,           # below the fan's base plane
    slot_front_from_box=10.15, # slot front end behind the box front edge
    box_depth=63.5,            # fan footprint front-to-back
    # ribs (calibrated: print #4 fit + one 0.1 click)
    rib_gap_at_peak=40.3,      # inner-edge gap between ribs AT THE PEAK (datum)
    rib_len=22.0,
    rib_h=2.0,
    clearance_side=0.15,
    # slab
    slab_w=56.0,               # across (X)
    slab_front=23.5,           # +Y extent (1.9 ahead of the rib fronts)
    slab_back=-14.5,           # -Y extent (11 mm of wall behind the thread)
    slab_t=10.0,               # approved ~10 mm stack; thread lives inside it
    notch_w=8.0,               # FRONT marker notch, cut through the front edge
    notch_d=2.0,
    foot_chamfer=0.4,          # elephant's-foot relief, outer bottom edges only
    # 1/4-20 socket (blind, opens to the bed/tripod side at z=0)
    thread_major=6.5,          # 6.35 nominal + printed-fit allowance
    thread_pitch=1.27,         # 20 TPI
    hole_depth=8.0,
    thread_len=7.0,
    mouth_chamfer_r=1.2,       # cone relief at the mouth (kills elephant's foot)
)


def slot_width(p: dict, d: float) -> float:
    """Slot width at distance d behind the slot's front end."""
    if d <= p["slot_peak_d"]:
        f, w = p["slot_front_w"], p["slot_peak_w"]
        return f + (w - f) * d / p["slot_peak_d"]
    return p["slot_peak_w"] - p["slot_taper_slope"] * (d - p["slot_peak_d"])


def _rib(p: dict):
    """One rib: kite plan profile extruded rib_h up, local origin at its center."""
    c, L = p["clearance_side"], p["rib_len"]
    stations = [0.0, p["slot_peak_d"], L]
    pts = [(d, slot_width(p, d) - 2 * c) for d in stations]
    half_l = L / 2.0
    left = [(-w / 2.0, half_l - d) for d, w in pts]
    right = [(w / 2.0, half_l - d) for d, w in reversed(pts)]
    return extrude(Polygon(*(left + right), align=None), amount=p["rib_h"])


def build(spec: dict | None = None):
    p = {**PARAMS, **(spec or {})}
    depth = p["slab_front"] - p["slab_back"]
    part = Pos(0, (p["slab_front"] + p["slab_back"]) / 2, 0) * Box(
        p["slab_w"], depth, p["slab_t"], align=_CCM)
    # ribs: front ends at the slot fronts, centerlines from the inner-gap datum
    rib_peak_w = slot_width(p, p["slot_peak_d"]) - 2 * p["clearance_side"]
    cx = p["rib_gap_at_peak"] / 2.0 + rib_peak_w / 2.0
    rib_front_y = p["box_depth"] / 2.0 - p["slot_front_from_box"]
    rib_cy = rib_front_y - p["rib_len"] / 2.0
    for sx in (-cx, cx):
        part += Pos(sx, rib_cy, p["slab_t"]) * _rib(p)
    # FRONT marker notch through the front edge
    part -= Pos(0, p["slab_front"] - p["notch_d"] / 2, 0) * Box(
        p["notch_w"], p["notch_d"] + 0.2, p["slab_t"], align=_CCM)
    # 1/4-20 socket: hole at major dia, fuse the internal thread, relieve the mouth
    part -= Cylinder(radius=p["thread_major"] / 2, height=p["hole_depth"],
                     align=_CCM)
    thread = IsoThread(major_diameter=p["thread_major"], pitch=p["thread_pitch"],
                       length=p["thread_len"], external=False,
                       end_finishes=("fade", "fade"))
    tz = thread.bounding_box().min.Z
    part += Pos(0, 0, -tz) * thread
    r0 = p["thread_major"] / 2 + p["mouth_chamfer_r"]
    part -= Cone(bottom_radius=r0, top_radius=p["thread_major"] / 2 - 0.2,
                 height=p["mouth_chamfer_r"] + 0.2, align=_CCM)
    # elephant's-foot relief on the outer (straight) bottom edges only
    bottom = part.faces().sort_by(Axis.Z)[0]
    part = chamfer(bottom.edges().filter_by(GeomType.LINE),
                   length=p["foot_chamfer"])
    return part


part = build()

if __name__ == "__main__":
    bb = part.bounding_box()
    print("bbox", bb.size, "volume mm^3", round(part.volume, 1))
    p = PARAMS
    w = slot_width(p, p["slot_peak_d"]) - 2 * p["clearance_side"]
    cx = p["rib_gap_at_peak"] / 2 + w / 2
    print(f"rib centerlines +/-{cx:.3f}  inner gap {2*(cx-w/2):.2f}  peak width {w:.2f}")
    print(f"thread: 1/4-20 (major {p['thread_major']}, pitch {p['thread_pitch']}), "
          f"{p['thread_len']/p['thread_pitch']:.1f} turns")
