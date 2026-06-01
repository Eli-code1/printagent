"""Angled stand for a phone, tablet, sign, or book: a truncated wedge whose sloped
top holds the item and whose tall front face acts as the lip. The wedge is truncated
to a finite front height, so there is no feather edge (a sharp taper to zero is a
knife edge that will not print), and the sloped rest faces up, so it prints with no
downward overhang. build(spec) -> Part."""
from __future__ import annotations
from build123d import Align, Plane, Polygon, Pos, extrude

DEFAULTS = dict(width=80.0, base_depth=70.0, back_h=55.0, front_h=8.0)


def build(spec: dict | None = None):
    p = {**DEFAULTS, **(spec or {})}
    w, bd, bh, fh = p["width"], p["base_depth"], p["back_h"], p["front_h"]
    profile = Plane.XZ * Polygon((0, 0), (bd, 0), (bd, fh), (0, bh), align=None)
    return Pos(0, -w / 2, 0) * extrude(profile, amount=w)
