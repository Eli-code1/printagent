"""Structured part spec — the output of the Step 0 clarifier and the input to generation.
Fill it after clarifying; record assumptions you made so the loop and the user can see them."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict


@dataclass
class Fit:
    feature: str          # e.g. "M3 fastener hole", "shaft Ø8"
    kind: str             # "clearance" | "press" | "fastened" | "print_in_place"
    nominal_mm: float


@dataclass
class PartSpec:
    function: str                              # what the part does / what it joins
    envelope_mm: tuple[float, float, float]    # max bounding box it must fit
    driving_dims: dict = field(default_factory=dict)
    fits: list = field(default_factory=list)   # list[Fit]
    principal_load: str = "none"               # description + direction; drives orientation
    printer: str = "generic"
    material: str = "PLA"
    nozzle_mm: float = 0.4
    layer_height_mm: float = 0.2
    profile: str = "structural"                # "cosmetic" | "structural"
    assumptions: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
