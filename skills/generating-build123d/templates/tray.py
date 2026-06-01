"""Shallow open-top tray with optional dividers. The open top means no enclosed
void; dividers span the full footprint so the part stays one solid.
build(spec) -> Part."""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build123d import Align, Box, Pos

DEFAULTS = dict(inner_w=120.0, inner_d=80.0, inner_h=25.0, wall=2.5, base=2.5,
                div_x=1, div_y=0)

_C = (Align.CENTER, Align.CENTER, Align.MIN)


def build(spec: dict | None = None):
    p = {**DEFAULTS, **(spec or {})}
    iw, idp, ih, wall, base = (p["inner_w"], p["inner_d"], p["inner_h"], p["wall"],
                               p["base"])
    ow, od = iw + 2 * wall, idp + 2 * wall
    part = Box(ow, od, ih + base, align=_C) - (Pos(0, 0, base) * Box(iw, idp, ih + 1.0, align=_C))
    for i in range(p["div_x"]):
        x = -iw / 2 + (i + 1) * iw / (p["div_x"] + 1)
        part = part + (Pos(x, 0, base) * Box(wall, od, ih, align=_C))
    for j in range(p["div_y"]):
        y = -idp / 2 + (j + 1) * idp / (p["div_y"] + 1)
        part = part + (Pos(0, y, base) * Box(ow, wall, ih, align=_C))
    return part
