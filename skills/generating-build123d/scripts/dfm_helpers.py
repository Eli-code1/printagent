"""Vetted, DFM-correct build123d part helpers. Compose these instead of free-handing
geometry — each one bakes in the rule numbers so the result tends to pass the gate.
Kernel-fragile ops are wrapped with a reduced-parameter retry."""
from __future__ import annotations
from build123d import (Align, Cylinder, Plane, Pos, chamfer, offset)
from fdm_params import HEATSET_PILOT_MM, clearance_hole_dia


def heatset_boss(insert: str = "M3", height: float = 8.0, wall: float = 2.0):
    """Cylindrical boss with a pilot bore sized for a heat-set insert. Wall >= 2 mm
    around the insert per DFM. Returns a solid aligned with its base at z=0."""
    pilot = HEATSET_PILOT_MM[insert]
    base = (Align.CENTER, Align.CENTER, Align.MIN)
    boss = Cylinder(radius=pilot / 2 + wall, height=height, align=base)
    bore = Cylinder(radius=pilot / 2, height=height, align=base)
    return boss - bore


def clearance_hole(part, location, screw: str = "M3", depth: float = 1000.0,
                   direction_z: bool = True):
    """Subtract a screw clearance hole at `location` (x, y, z). Default cuts straight
    down the Z axis through the part."""
    dia = clearance_hole_dia(screw)
    cutter = Cylinder(radius=dia / 2, height=depth,
                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part - (Pos(*location) * cutter)


def shell(part, thickness: float, open_face=None):
    """Hollow a solid to a uniform wall. The gate enforces thickness >= min wall; pick
    thickness >= 4 x line width for structural parts. `open_face` is a Face to leave open."""
    try:
        return offset(part, amount=-abs(thickness), openings=open_face or [])
    except Exception:
        # internal corners too sharp for this thickness — try a slightly thinner wall once
        return offset(part, amount=-abs(thickness) * 0.8, openings=open_face or [])


def chamfer_bottom_edges(part, length: float = 0.5):
    """Mitigate elephant's foot with a 45-degree chamfer on the bottom face's edges."""
    bottom = part.faces().sort_by_distance((0, 0, -1e6))[0] if hasattr(
        part.faces(), "sort_by_distance") else part.faces().sort_by()[0]
    try:
        return chamfer(bottom.edges(), length=length)
    except Exception:
        return chamfer(bottom.edges(), length=length * 0.5)


def add_vent(part, at_xyz, diameter: float = 3.0, depth: float = 1000.0):
    """Drill a vertical drain/vent into an enclosed cavity at `at_xyz`. Forced to >= 3 mm."""
    d = max(diameter, 3.0)
    cutter = Cylinder(radius=d / 2, height=depth,
                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    return part - (Pos(*at_xyz) * cutter)


def mouse_ears(corner_xy, z: float = 0.0, diameter: float = 10.0, thickness: float = 0.4):
    """A thin adhesion disk to place at a sharp corner of a shrink-prone part."""
    return Pos(corner_xy[0], corner_xy[1], z) * Cylinder(
        radius=diameter / 2, height=thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
