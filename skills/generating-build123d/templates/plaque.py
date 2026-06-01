"""Plaque: a flat plate with a raised border around an open recess and a hang hole.
Prints flat with vertical border walls. build(spec) -> Part."""
from __future__ import annotations
from build123d import Align, Box, Cylinder, Pos

DEFAULTS = dict(width=100.0, height=70.0, thickness=3.0, border=4.0, border_h=2.0,
                hang_dia=6.0)

_C = (Align.CENTER, Align.CENTER, Align.MIN)


def build(spec: dict | None = None):
    p = {**DEFAULTS, **(spec or {})}
    W, Hh, t, b, bh, hd = (p["width"], p["height"], p["thickness"], p["border"],
                           p["border_h"], p["hang_dia"])
    plate = Box(W, Hh, t, align=_C)
    frame = Pos(0, 0, t) * (Box(W, Hh, bh, align=_C)
                            - Box(W - 2 * b, Hh - 2 * b, bh + 1.0, align=_C))
    part = plate + frame
    part = part - (Pos(0, Hh / 2 - b - hd, 0)
                   * Cylinder(radius=hd / 2, height=t + bh + 2.0, align=_C))
    return part
