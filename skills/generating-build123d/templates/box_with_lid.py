"""Box with a friction-fit lid, printed as two parts. build(spec) returns the box
body (open top, no enclosed void); build_lid(spec) returns the lid, oriented flat
plate down with the locating plug pointing up so it prints without supports. The
plug is undersized by `clearance` so it drops into the body. Composes dfm_helpers."""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build123d import Align, Box, Pos
import dfm_helpers as H

DEFAULTS = dict(inner_w=60.0, inner_d=40.0, inner_h=30.0, wall=2.5, base=2.5,
                lid_h=3.0, lip_h=4.0, clearance=0.2, foot_chamfer=0.6)

_C = (Align.CENTER, Align.CENTER, Align.MIN)


def build(spec: dict | None = None):
    p = {**DEFAULTS, **(spec or {})}
    iw, idp, ih, wall, base = (p["inner_w"], p["inner_d"], p["inner_h"],
                               p["wall"], p["base"])
    outer = Box(iw + 2 * wall, idp + 2 * wall, ih + base, align=_C)
    cavity = Pos(0, 0, base) * Box(iw, idp, ih + 1.0, align=_C)
    part = outer - cavity
    if p["foot_chamfer"]:
        part = H.chamfer_bottom_edges(part, p["foot_chamfer"])
    return part


def build_lid(spec: dict | None = None):
    p = {**DEFAULTS, **(spec or {})}
    iw, idp, wall = p["inner_w"], p["inner_d"], p["wall"]
    lid_h, lip_h, clr = p["lid_h"], p["lip_h"], p["clearance"]
    plate = Box(iw + 2 * wall, idp + 2 * wall, lid_h, align=_C)        # on the bed
    plug = Pos(0, 0, lid_h) * Box(iw - clr, idp - clr, lip_h, align=_C)  # points up
    return plate + plug
