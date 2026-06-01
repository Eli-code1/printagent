"""Open-top holder or organizer: a rectangular container sized by its inner cavity.
The open top means there is no enclosed void to trap material. Parametric; composes
dfm_helpers. build(spec) returns a single printable Part with its base on the bed."""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build123d import Align, Box, Pos
import dfm_helpers as H

DEFAULTS = dict(inner_w=60.0, inner_d=40.0, inner_h=50.0, wall=2.5, base=2.5,
                foot_chamfer=0.6)

_C = (Align.CENTER, Align.CENTER, Align.MIN)


def build(spec: dict | None = None):
    p = {**DEFAULTS, **(spec or {})}
    iw, idp, ih, wall, base = (p["inner_w"], p["inner_d"], p["inner_h"],
                               p["wall"], p["base"])
    outer = Box(iw + 2 * wall, idp + 2 * wall, ih + base, align=_C)
    cavity = Pos(0, 0, base) * Box(iw, idp, ih + 1.0, align=_C)   # +1 opens the top
    part = outer - cavity
    if p["foot_chamfer"]:
        part = H.chamfer_bottom_edges(part, p["foot_chamfer"])
    return part
