"""Flat mounting plate with a grid of screw clearance holes. Prints flat with
vertical hole walls. build(spec) -> Part."""
from __future__ import annotations
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from build123d import Align, Box
import dfm_helpers as H

DEFAULTS = dict(width=80.0, depth=60.0, thickness=4.0, nx=3, ny=2, margin=10.0,
                screw="M4")

_C = (Align.CENTER, Align.CENTER, Align.MIN)


def build(spec: dict | None = None):
    p = {**DEFAULTS, **(spec or {})}
    W, D, t, nx, ny, m = (p["width"], p["depth"], p["thickness"], p["nx"], p["ny"],
                          p["margin"])
    part = Box(W, D, t, align=_C)
    xs = [-W / 2 + m + i * (W - 2 * m) / (nx - 1) for i in range(nx)] if nx > 1 else [0.0]
    ys = [-D / 2 + m + j * (D - 2 * m) / (ny - 1) for j in range(ny)] if ny > 1 else [0.0]
    for x in xs:
        for y in ys:
            part = H.clearance_hole(part, (x, y, 0.0), screw=p["screw"])
    return part
