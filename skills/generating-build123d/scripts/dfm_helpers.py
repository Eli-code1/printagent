"""Vetted, DFM-correct build123d part helpers. Compose these instead of free-handing
geometry, each one bakes in the rule numbers so the result tends to pass the gate.
Kernel-fragile ops are wrapped with a reduced-parameter retry."""
from __future__ import annotations
import math
from build123d import (Align, Box, Cone, Cylinder, Plane, Polygon, Pos,
                       RegularPolygon, Rot, chamfer, extrude, offset)
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
        # internal corners too sharp for this thickness, try a slightly thinner wall once
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


# --- fastener dimension tables (mm), provenance in references/dfm_constants.md
# Socket-head cap screw heads (ISO 4762): (head_dia, head_height)
SOCKET_HEAD_MM = {"M2": (3.8, 2.0), "M2.5": (4.5, 2.5), "M3": (5.5, 3.0),
                  "M4": (7.0, 4.0), "M5": (8.5, 5.0), "M6": (10.0, 6.0)}
# Countersink flat-head major diameter, 90 deg (ISO 10642), approx
CSK_HEAD_MM = {"M2": 4.0, "M2.5": 5.0, "M3": 6.0, "M4": 8.0, "M5": 10.0, "M6": 12.0}
# Plastic tap / self-tap pilot diameters, approx
TAP_DRILL_MM = {"M2": 1.6, "M2.5": 2.05, "M3": 2.5, "M4": 3.3, "M5": 4.2, "M6": 5.0}
# Hex nut across-flats and thickness (ISO 4032): (across_flats, thickness)
HEX_NUT_MM = {"M2": (4.0, 1.6), "M2.5": (5.0, 2.0), "M3": (5.5, 2.4),
              "M4": (7.0, 3.2), "M5": (8.0, 4.7), "M6": (10.0, 5.2)}

_MIN = (Align.CENTER, Align.CENTER, Align.MIN)


def counterbore_hole(part, location, screw: str = "M3", through: float = 1000.0,
                     clearance: float = 0.4):
    """Through clearance hole plus a top recess for a socket-head cap screw head.
    Cuts down +Z from `location`; recess dimensions follow ISO 4762."""
    clr = clearance_hole_dia(screw)
    head_d, head_h = SOCKET_HEAD_MM.get(screw, (clr * 1.8, clr))
    shaft = Cylinder(radius=clr / 2, height=through, align=_MIN)
    recess = Cylinder(radius=(head_d + clearance) / 2, height=head_h + 0.2, align=_MIN)
    return part - (Pos(*location) * shaft) - (Pos(*location) * recess)


def countersink_hole(part, location, screw: str = "M3", through: float = 1000.0):
    """Through clearance hole plus a 90-degree conical recess for a flat-head screw."""
    clr = clearance_hole_dia(screw)
    head_d = CSK_HEAD_MM.get(screw, clr * 2.0)
    csk_depth = (head_d - clr) / 2.0                       # 90-degree cone geometry
    shaft = Cylinder(radius=clr / 2, height=through, align=_MIN)
    cone = Cone(bottom_radius=clr / 2, top_radius=head_d / 2, height=csk_depth, align=_MIN)
    return part - (Pos(*location) * shaft) - (Pos(*location) * cone)


def tap_hole(part, location, screw: str = "M3", depth: float = 1000.0):
    """Pilot hole sized for cutting or self-tapping a thread directly into plastic."""
    d = TAP_DRILL_MM.get(screw, clearance_hole_dia(screw) * 0.8)
    return part - (Pos(*location) * Cylinder(radius=d / 2, height=depth, align=_MIN))


def captive_nut_pocket(part, location, screw: str = "M3", through: float = 1000.0,
                       clearance: float = 0.3):
    """Hex recess to trap a standard nut, plus a through clearance hole below it.
    The recess opens upward from `location`; orient the part so the nut drops in."""
    af, thick = HEX_NUT_MM.get(screw, (clearance_hole_dia(screw) * 1.8, 2.4))
    circ_r = (af + clearance) / math.sqrt(3.0)             # circumradius from across-flats
    hexagon = extrude(RegularPolygon(radius=circ_r, side_count=6), amount=thick + 0.2)
    clr = clearance_hole_dia(screw)
    shaft = Cylinder(radius=clr / 2, height=through, align=_MIN)
    return part - (Pos(*location) * hexagon) - (Pos(*location) * shaft)


def add_standoff(part, location, height: float, screw: str = "M3", wall: float = 2.0):
    """Add a hollow cylindrical standoff: a spacer with a through clearance bore."""
    clr = clearance_hole_dia(screw)
    outer = Cylinder(radius=clr / 2 + wall, height=height, align=_MIN)
    bore = Cylinder(radius=clr / 2, height=height, align=_MIN)
    return part + (Pos(*location) * (outer - bore))


def add_rib(part, start_xy, end_xy, height: float, thickness: float = 1.6, z: float = 0.0):
    """Add a straight reinforcing rib (a thin upright wall) between two points.
    Default thickness is about four line widths at a 0.4 mm nozzle."""
    dx, dy = end_xy[0] - start_xy[0], end_xy[1] - start_xy[1]
    length = math.hypot(dx, dy)
    angle = math.degrees(math.atan2(dy, dx))
    mid = ((start_xy[0] + end_xy[0]) / 2, (start_xy[1] + end_xy[1]) / 2, z)
    rib = Box(length, thickness, height, align=_MIN)
    return part + (Pos(*mid) * Rot(0, 0, angle) * rib)


def add_gusset(part, corner_xy, run: float = 10.0, rise: float = 10.0,
               thickness: float = 1.6, z: float = 0.0, angle: float = 0.0):
    """Add a right-triangle gusset bracing a vertical wall against the base. The
    triangle stands in a vertical plane; `angle` (degrees) rotates it about Z."""
    tri = Plane.XZ * Polygon((0, 0), (run, 0), (0, rise), align=None)
    gusset = extrude(tri, amount=thickness)
    return part + (Pos(corner_xy[0], corner_xy[1], z) * Rot(0, 0, angle) * gusset)


def slot_hole(part, location, length: float, width: float, depth: float = 1000.0,
              angle: float = 0.0):
    """Cut a rounded slot (a stadium hole). `length` is the centre-to-centre span of
    the two end radii, so the total opening is length + width."""
    r = width / 2.0
    cutter = (Box(length, width, depth, align=_MIN)
              + (Pos(length / 2, 0, 0) * Cylinder(radius=r, height=depth, align=_MIN))
              + (Pos(-length / 2, 0, 0) * Cylinder(radius=r, height=depth, align=_MIN)))
    return part - (Pos(*location) * Rot(0, 0, angle) * cutter)
