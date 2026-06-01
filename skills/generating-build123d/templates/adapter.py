"""Tubular adapter or coupler: a straight sleeve with a through bore, for joining or
sleeving round parts. Prints vertically with no overhang. build(spec) -> Part."""
from __future__ import annotations
from build123d import Align, Cylinder

DEFAULTS = dict(outer_dia=30.0, bore_dia=24.0, length=25.0)

_C = (Align.CENTER, Align.CENTER, Align.MIN)


def build(spec: dict | None = None):
    p = {**DEFAULTS, **(spec or {})}
    return (Cylinder(radius=p["outer_dia"] / 2, height=p["length"], align=_C)
            - Cylinder(radius=p["bore_dia"] / 2, height=p["length"], align=_C))
