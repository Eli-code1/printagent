"""Overhang gate. Measures each downward-facing surface's angle from vertical
(0deg = vertical wall, 90deg = flat ceiling) and flags area steeper than the
printer's safe threshold. Warning severity: overhangs are support-able."""
from __future__ import annotations
import numpy as np


def check_overhangs(mesh, max_overhang_deg=45.0, build_dir=(0, 0, 1)):
    n = mesh.face_normals
    areas = mesh.area_faces
    bz = np.asarray(build_dir, float)
    bz /= np.linalg.norm(bz)
    nz = n @ bz                                   # normal component along build dir
    down = nz < -1e-6                             # downward-facing faces only

    # angle of the surface from vertical = arcsin(|nz|)  (normal _|_ surface)
    oh_deg = np.degrees(np.arcsin(np.clip(np.abs(nz), 0.0, 1.0)))
    violating = down & (oh_deg > max_overhang_deg)

    viol_area = float(areas[violating].sum())
    return {"name": "overhangs", "passed": bool(viol_area <= 1e-6),
            "severity": "warning", "threshold_deg_from_vertical": max_overhang_deg,
            "worst_overhang_deg": round(float(oh_deg[down].max()) if down.any() else 0.0, 1),
            "overhanging_area_mm2": round(viol_area, 2),
            "downward_area_mm2": round(float(areas[down].sum()), 2),
            "detail": ("Surfaces steeper than the threshold need support or redesign; "
                       "prefer reorienting the build or chamfering downward edges.")}


if __name__ == "__main__":
    import sys
    import json
    from geometry_io import load_mesh, sanitize
    m, _ = sanitize(load_mesh(sys.argv[1]))
    thr = float(sys.argv[2]) if len(sys.argv) > 2 else 45.0
    print(json.dumps(check_overhangs(m, thr), indent=2))
