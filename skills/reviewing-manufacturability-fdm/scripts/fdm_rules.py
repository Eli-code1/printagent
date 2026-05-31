"""Machine-readable FDM DFM defaults and scaling functions.

Single source of numeric truth for the manufacturability gates. Human-readable
rationale and sources live in ../references/fdm-rules.md. Defaults assume a
0.4 mm nozzle / 0.2 mm layer height unless a scaling function is provided.
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, asdict

PROFILES_PATH = os.path.join(os.path.dirname(__file__), "printer_profiles.json")


def line_width(nozzle: float) -> float:
    return nozzle  # single-perimeter extrusion width ~= nozzle diameter


def min_wall_cosmetic(nozzle: float) -> float:
    return round(2 * line_width(nozzle), 3)


def min_wall_structural(nozzle: float) -> float:
    return round(4 * line_width(nozzle), 3)


def min_wall_z(layer_height: float) -> float:
    return round(4 * layer_height, 3)


def print_in_place_gap(layer_height: float) -> float:
    return max(0.3, round(1.5 * layer_height, 3))


def elephant_foot_chamfer(first_layer_h: float = 0.2) -> float:
    return round(max(0.4, 3 * first_layer_h), 3)


# Heat-set insert pilot bores for PLA/PETG (OD - 0.1 rule baked in).
HEATSET_PILOT_MM = {"M2": 3.2, "M2.5": 3.6, "M3": 4.0, "M4": 5.6, "M5": 6.4}


def load_profile(name: str) -> dict:
    with open(PROFILES_PATH) as f:
        profiles = json.load(f)
    return profiles[name if name in profiles else "generic"]


@dataclass
class Thresholds:
    nozzle: float
    layer_height: float
    profile: str            # "cosmetic" | "structural"
    min_wall: float
    min_wall_z: float
    max_overhang_deg: float  # measured from vertical
    enclosed_void_min_mm3: float

    def to_dict(self) -> dict:
        return asdict(self)


def resolve_thresholds(nozzle: float = 0.4, layer_height: float = 0.2,
                       profile: str = "structural", printer: str | None = None) -> Thresholds:
    prof = load_profile(printer) if printer else {}
    mw = (min_wall_structural(nozzle) if profile == "structural"
          else min_wall_cosmetic(nozzle))
    return Thresholds(
        nozzle=nozzle,
        layer_height=layer_height,
        profile=profile,
        min_wall=mw,
        min_wall_z=min_wall_z(layer_height),
        max_overhang_deg=float(prof.get("max_overhang_deg", 45.0)),
        enclosed_void_min_mm3=1.0,
    )
