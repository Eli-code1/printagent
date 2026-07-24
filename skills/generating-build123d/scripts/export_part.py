"""Vetted exporter. build123d is millimetre-native, so STEP carries mm and STL is mm by
convention. STEP is the lossless archive and gives the gate its B-rep; STL feeds the mesh
checks. Rich 3MF export for the slicer lives in slicing-handoff-bambu.

STEP product names come from build123d labels; an unlabeled part exports as
PRODUCT('COMPOUND'), which CAD importers (Onshape, Fusion, FreeCAD) show as an anonymous
part. Labels are therefore guaranteed here: the part is named (explicit `name`, existing
label, or the stem's basename, in that order) and unlabeled compound children get
"<name>_1..n" so multi-body imports arrive as individually named parts."""
from __future__ import annotations
import os
from build123d import export_step, export_stl


def export_part(part, stem: str, also_stl: bool = True,
                tolerance: float = 0.01, angular_tolerance: float = 0.1,
                name: str | None = None) -> str:
    if name:
        part.label = name
    elif not getattr(part, "label", ""):
        part.label = os.path.basename(stem)
    for i, child in enumerate(getattr(part, "children", ()) or (), 1):
        if not child.label:
            child.label = f"{part.label}_{i}"
    step_path = f"{stem}.step"
    export_step(part, step_path)
    if also_stl:
        export_stl(part, f"{stem}.stl", tolerance=tolerance,
                   angular_tolerance=angular_tolerance)
    return step_path
