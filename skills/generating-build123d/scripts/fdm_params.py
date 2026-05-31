"""Local subset of FDM numbers needed by the part helpers. Mirrors the authoritative
set in reviewing-manufacturability-fdm/references/fdm-rules.md; kept local so this skill
is self-contained. Keep the two in sync if you change a value."""
from __future__ import annotations

# Heat-set insert pilot bores, PLA/PETG (OD - 0.1 rule baked in).
HEATSET_PILOT_MM = {"M2": 3.2, "M2.5": 3.6, "M3": 4.0, "M4": 5.6, "M5": 6.4}

# Metric clearance holes, "normal" fit.
CLEARANCE_HOLE_MM = {"M2": 2.4, "M2.5": 2.9, "M3": 3.4, "M4": 4.5, "M5": 5.5, "M6": 6.6}


def line_width(nozzle: float = 0.4) -> float:
    return nozzle


def min_wall(nozzle: float = 0.4, perimeters: int = 4) -> float:
    return round(perimeters * line_width(nozzle), 3)


def clearance_hole_dia(screw: str) -> float:
    return CLEARANCE_HOLE_MM[screw]


def print_in_place_gap(layer_h: float = 0.2) -> float:
    return max(0.3, round(1.5 * layer_h, 3))


def elephant_foot_chamfer(first_layer_h: float = 0.2) -> float:
    return round(max(0.4, 3 * first_layer_h), 3)
