"""Mass, center of mass, inertia, and slenderness. trimesh-based (density 1 -> mass==volume),
scaled by material density and a rough infill factor."""
from __future__ import annotations
import numpy as np


def mass_properties(mesh, density_g_cm3=1.24, infill=0.25):
    if not mesh.is_watertight:
        return {"name": "mass_properties", "passed": None,
                "detail": "mesh not watertight; mass properties unreliable"}
    vol_mm3 = float(mesh.volume)
    vol_cm3 = vol_mm3 / 1000.0
    solid_g = vol_cm3 * density_g_cm3
    # crude infill-scaled estimate: solid walls + infill-fraction core; ~0.35-0.6 of solid
    est_g = solid_g * (0.35 + 0.65 * float(infill))
    com = [round(float(c), 2) for c in mesh.center_mass]
    obb = np.sort(mesh.bounding_box_oriented.extents)
    slender = round(float(obb[-1] / max(obb[0], 1e-6)), 1)
    return {"name": "mass_properties", "passed": True,
            "volume_mm3": round(vol_mm3, 1),
            "solid_mass_g": round(solid_g, 1),
            "estimated_mass_g": round(est_g, 1),
            "center_of_mass_mm": com,
            "principal_inertia": [round(float(v), 1) for v in mesh.principal_inertia_components],
            "obb_slenderness_ratio": slender,
            "detail": "Mass is solid-density estimate; actual depends on infill and walls."}
