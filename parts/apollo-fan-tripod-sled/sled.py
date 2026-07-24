"""Phase-2 tripod sled for the inbio Apollo Fan.

Full sled per the spec: plate + the two kite ribs that drop into the fan's tapered
base slots, plus a 1/4-20 printed-thread tripod socket in a stubby boss under the
plate. The rib/slot fit geometry is imported from coupon.py so the four fit prints
that converged it (gap datum 40.2, clearance 0.15/side) carry over unchanged; the
rib stays at the coupon's validated 22 mm, not the spec's pre-test ~30 mm nominal.
Spec: docs/superpowers/specs/2026-07-23-apollo-fan-tripod-sled-design.md

Exported in print orientation (+Z up, boss on the bed, ribs up): the plate
underside needs supports (7 mm table-top over the boss), which keeps the rib fit
surfaces and the fan-contact face pristine and the thread axis vertical. In use it
is the same way up: boss to the tripod, ribs into the fan.

Fan-relative placement: slot/rib front ends sit 10.15 mm behind the fan's front
edge; the boss centers under the fan's balance point 32 mm behind it, so the boss
is 21.85 mm behind the rib front. The plate front edge rides 4 mm ahead of the rib
front (6.15 mm behind the fan's front face - fully tucked under).
"""
from __future__ import annotations
import os
import sys

from bd_warehouse.thread import IsoThread
from build123d import (Align, Axis, Box, Cylinder, GeomType, Pos, SortBy, chamfer)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coupon import PARAMS as FIT, _rib, slot_width  # noqa: E402

PARAMS = dict(
    # plate (top face = fan base plane)
    plate_w=56.0,              # across (X)
    plate_d=44.0,              # front-to-back (Y)
    plate_t=3.0,
    rib_front_y=18.0,          # rib front ends here; 4 mm behind the plate front edge
    notch_w=8.0,               # center notch in the front edge marking FRONT (+Y)
    notch_d=2.0,
    # tripod boss + printed 1/4-20 socket
    boss_d=16.0,
    boss_h=7.0,                # under-fan stack = boss_h + plate_t = 10 mm
    boss_behind_rib_front=21.85,   # fan balance point 32 - slot front 10.15
    thread_major=6.35,         # 1/4-20 UNC nominal
    thread_pitch=1.27,         # 20 TPI
    thread_fit=0.30,           # diametral allowance for FDM female thread; fit knob
    socket_depth=8.0,          # blind; leaves a 2 mm cap under the plate top
    mouth_chamfer=1.2,         # screw lead-in, doubles as elephant's foot at the bore
    foot_chamfer=0.4,          # elephant's-foot relief, boss bottom outer edge
    simple_thread=False,       # True = smooth cylinder instead of thread geometry
                               # (fast rebuilds/renders and gate diagnostics only)
)


def build(spec: dict | None = None):
    p = {**PARAMS, **(spec or {})}
    z_plate = p["boss_h"]                      # plate bottom
    z_top = z_plate + p["plate_t"]             # fan base plane

    plate = Pos(0, 0, z_plate) * Box(p["plate_w"], p["plate_d"], p["plate_t"],
                                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    boss_y = p["rib_front_y"] - p["boss_behind_rib_front"]
    part = plate + Pos(0, boss_y, 0) * Cylinder(
        p["boss_d"] / 2.0, p["boss_h"],
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # ribs: identical placement math to the coupon (same datum, same clearance)
    rib_peak_w = slot_width(FIT, FIT["slot_peak_d"]) - 2 * FIT["clearance_side"]
    cx = FIT["rib_gap_at_peak"] / 2.0 + rib_peak_w / 2.0
    rib_dy = p["rib_front_y"] - FIT["rib_len"] / 2.0   # _rib() is centered on Y
    for sx in (-cx, cx):
        part += Pos(sx, rib_dy, z_top) * _rib(FIT)

    # FRONT marker: notch cut through the plate at the center of the front edge
    part -= Pos(0, p["plate_d"] / 2 - p["notch_d"] / 2, z_plate - 0.1) * Box(
        p["notch_w"], p["notch_d"] + 0.2, p["plate_t"] + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # tripod socket: bore at the thread's major diameter, blind
    bore_d = p["thread_major"] + p["thread_fit"]
    part -= Pos(0, boss_y, 0) * Cylinder(
        bore_d / 2.0, p["socket_depth"],
        align=(Align.CENTER, Align.CENTER, Align.MIN))

    # chamfers last (kernel-fragile): screw lead-in at the mouth, then foot relief
    bottom_circles = (part.edges().filter_by(GeomType.CIRCLE)
                      .group_by(Axis.Z)[0].sort_by(SortBy.RADIUS))
    part = chamfer(bottom_circles[0], length=p["mouth_chamfer"])       # bore mouth
    bottom_circles = (part.edges().filter_by(GeomType.CIRCLE)
                      .group_by(Axis.Z)[0].sort_by(SortBy.RADIUS))
    part = chamfer(bottom_circles[-1], length=p["foot_chamfer"])       # boss rim

    # modeled thread, fused into the bore (interference handles the shared wall);
    # starts above the mouth chamfer, fades below the blind end
    if not p["simple_thread"]:
        thread_z0 = p["mouth_chamfer"] + 0.2
        thread = IsoThread(major_diameter=bore_d, pitch=p["thread_pitch"],
                           length=p["socket_depth"] - thread_z0, external=False,
                           end_finishes=("square", "fade"))
        part += Pos(0, boss_y, thread_z0) * thread

    part.label = "apollo_sled"
    return part


part = build()

if __name__ == "__main__":
    bb = part.bounding_box()
    turns = (PARAMS["socket_depth"] - PARAMS["mouth_chamfer"] - 0.2) / PARAMS["thread_pitch"]
    print("bbox", bb.size, "volume mm^3", round(part.volume, 1))
    print("solids", len(part.solids()), "valid", part.is_valid,
          "thread turns", round(turns, 2))
