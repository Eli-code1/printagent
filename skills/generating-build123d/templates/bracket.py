"""Wall-mount L-bracket: a base flange and an upright flange braced by a gusset,
with mounting holes in both legs. Parametric; composes dfm_helpers so the result
tends to pass the gate. build(spec) returns a single printable Part oriented with
the base on the bed (+Z up)."""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build123d import Align, Box, Cylinder, Pos, Rot
import dfm_helpers as H
from fdm_params import clearance_hole_dia

DEFAULTS = dict(width=30.0, base_len=40.0, wall_height=35.0, thickness=3.0,
                screw="M3", base_holes=2, wall_holes=2, gusset=True, foot_chamfer=0.6)

_MIN = (Align.MIN, Align.CENTER, Align.MIN)


def _hole_ys(n, width, margin=8.0):
    if n <= 0:
        return []
    if n == 1:
        return [0.0]
    span = max(0.0, width - 2 * margin)
    return [-span / 2 + i * span / (n - 1) for i in range(n)]


def build(spec: dict | None = None):
    p = {**DEFAULTS, **(spec or {})}
    t, w, bl, wh = p["thickness"], p["width"], p["base_len"], p["wall_height"]
    clr = clearance_hole_dia(p["screw"])
    part = Box(bl, w, t, align=_MIN) + Box(t, w, wh, align=_MIN)

    for y in _hole_ys(p["base_holes"], w):                 # base holes, cut down Z
        part = H.clearance_hole(part, (bl * 0.72, y, 0.0), screw=p["screw"])
    for y in _hole_ys(p["wall_holes"], w):                 # wall holes, cut along +X
        part = part - (Pos(-t, y, wh * 0.6) * Rot(0, 90, 0)
                       * Cylinder(radius=clr / 2, height=3 * t,
                                  align=(Align.CENTER, Align.CENTER, Align.MIN)))
    if p["gusset"]:
        part = H.add_gusset(part, (t, -t / 2), run=bl * 0.4, rise=wh * 0.4,
                            thickness=t, z=0.0)
    if p["foot_chamfer"]:
        part = H.chamfer_bottom_edges(part, p["foot_chamfer"])
    return part
