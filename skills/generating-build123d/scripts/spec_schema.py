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
class Invariants:
    """Cheap, closed-form expectations checked against the built part BEFORE the
    expensive DFM gate. Any field left None is not checked."""
    bbox_min_mm: tuple = None               # lower bound on the (x, y, z) bounding box
    bbox_max_mm: tuple = None               # upper bound on the (x, y, z) bounding box
    volume_mm3: float = None                # expected volume (centre of the band)
    volume_tol: float = 0.30                # fractional tolerance on the volume
    solid_count: int = None                 # expected number of disjoint solids
    hole_count: int = None                  # expected number of through holes (by genus)
    watertight: bool = True                 # the mesh must be watertight
    planar_bottom: bool = None              # a flat face must sit on the build plane
    named_features: list = field(default_factory=list)


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
    invariants: Invariants = None              # expected, checked by the run_invariants pre-gate

    def to_dict(self) -> dict:
        return asdict(self)
