"""Wall hook: a back plate with two screw holes and a forward arm ending in an
upturned tip. In this orientation the arm reads as an overhang (a warning, not a
hard fail); the orientation step would lay it down to print. build(spec) -> Part."""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build123d import Align, Box, Cylinder, Pos, Rot
from fdm_params import clearance_hole_dia

DEFAULTS = dict(back_w=25.0, back_h=45.0, thickness=4.0, arm_len=28.0, tip_h=18.0,
                screw="M4")

_MIN = (Align.MIN, Align.CENTER, Align.MIN)


def build(spec: dict | None = None):
    p = {**DEFAULTS, **(spec or {})}
    t, bw, bh, al, th = (p["thickness"], p["back_w"], p["back_h"], p["arm_len"],
                         p["tip_h"])
    part = (Box(t, bw, bh, align=_MIN)
            + Pos(0, 0, bh - t) * Box(al + t, bw, t, align=_MIN)
            + Pos(al, 0, bh - t) * Box(t, bw, th, align=_MIN))
    clr = clearance_hole_dia(p["screw"])
    for z in (bh * 0.25, bh * 0.75):
        part = part - (Pos(-t, 0, z) * Rot(0, 90, 0)
                       * Cylinder(radius=clr / 2, height=3 * t,
                                  align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return part
