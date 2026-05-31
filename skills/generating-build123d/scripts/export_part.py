"""Vetted exporter. build123d is millimetre-native, so STEP carries mm and STL is mm by
convention. STEP is the lossless archive and gives the gate its B-rep; STL feeds the mesh
checks. Rich 3MF export for the slicer lives in slicing-handoff-bambu."""
from __future__ import annotations
from build123d import export_step, export_stl


def export_part(part, stem: str, also_stl: bool = True,
                tolerance: float = 0.01, angular_tolerance: float = 0.1) -> str:
    step_path = f"{stem}.step"
    export_step(part, step_path)
    if also_stl:
        export_stl(part, f"{stem}.stl", tolerance=tolerance,
                   angular_tolerance=angular_tolerance)
    return step_path
