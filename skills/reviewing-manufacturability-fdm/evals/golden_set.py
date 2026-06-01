"""Deterministic min-wall regression corpus.

Each case builds a parametric part with build123d and pins the expected min-wall
verdict in closed form. `run_evals.py` runs the gate against every case and fails
on any mismatch. This is what makes the gate trustworthy: it is proven against
known answers on every change, not smoke-tested by inspection on a single cube.

Every builder is deterministic and tiny. The threshold T is per case so the
sweep brackets the transition exactly.
"""
from __future__ import annotations
from build123d import Box, Cylinder, Pos, chamfer

T = 1.0  # default threshold for the wall sweep, in mm


def _plate(t):
    return Box(30, 30, t)


def _chamfered_block():
    b = Box(20, 20, 20)
    return chamfer(b.edges(), 2.0)


def _hollow_box(wall):
    return Box(40, 40, 24) - (Pos(0, 0, wall) * Box(40 - 2 * wall, 40 - 2 * wall, 24))


def _l_bracket():
    # Thick L (every wall >= 6 mm) with a concave inner corner. A single inward
    # ray from the inner faces can wrap around the corner and read thin; the cone
    # median plus the wraparound filter must still call this PASS.
    return Box(24, 24, 10) - (Pos(6, 6, 0) * Box(24, 24, 10))


# name -> (builder() -> Part, threshold_mm, expected_verdict in {PASS, FAIL})
CASES = [
    ("solid_cube_20mm",        lambda: Box(20, 20, 20),     T, "PASS"),
    ("plate_0p4mm",            lambda: _plate(0.4),         T, "FAIL"),
    ("plate_0p8mm",            lambda: _plate(0.8),         T, "FAIL"),
    ("plate_1p2mm",            lambda: _plate(1.2),         T, "PASS"),
    ("plate_2p0mm",            lambda: _plate(2.0),         T, "PASS"),
    ("plate_at_threshold_1p0", lambda: _plate(1.0),         T, "PASS"),
    ("plate_below_thresh_0p9", lambda: _plate(0.9),         T, "FAIL"),
    ("thin_fin_0p5mm",         lambda: Box(20, 0.5, 20),    T, "FAIL"),
    ("tall_thin_pin_d0p8",     lambda: Cylinder(0.4, 20),   T, "FAIL"),
    ("chamfered_block",        _chamfered_block,            T, "PASS"),
    ("hollow_box_2mm",         lambda: _hollow_box(2.0),    T, "PASS"),
    ("hollow_box_0p6mm",       lambda: _hollow_box(0.6),    T, "FAIL"),
    ("thick_l_bracket",        _l_bracket,                  T, "PASS"),
]
