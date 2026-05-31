"""Build-volume gate. Footprint + height vs the printer's usable envelope, Z up.
Reports an oriented-bounding-box hint and the first-layer footprint area."""
from __future__ import annotations
import numpy as np


def check_build_volume(mesh, bed_mm, usable_margin_mm=3.0):
    ext = mesh.extents                                   # [x, y, z] as oriented
    ux, uy, uz = (np.asarray(bed_mm, float) - usable_margin_mm)
    xy, bed_xy = sorted([ext[0], ext[1]]), sorted([ux, uy])
    fits = bool(ext[2] <= uz and xy[0] <= bed_xy[0] and xy[1] <= bed_xy[1])

    obb = np.sort(mesh.bounding_box_oriented.extents)
    reorient_hint = bool((not fits) and np.all(obb <= np.sort([ux, uy, uz])))

    footprint = None
    try:
        zmin = float(mesh.bounds[0, 2])
        sec = mesh.section(plane_origin=[0, 0, zmin + 1e-3], plane_normal=[0, 0, 1])
        if sec is not None:
            p2d, _ = sec.to_planar()
            footprint = round(float(sum(p.area for p in p2d.polygons_full)), 2)
    except Exception:
        pass

    return {"name": "build_volume", "passed": fits, "severity": "fail",
            "usable_envelope_mm": [round(ux, 1), round(uy, 1), round(uz, 1)],
            "aabb_extents_mm": [round(float(v), 1) for v in ext],
            "obb_extents_mm": [round(float(v), 1) for v in obb],
            "first_layer_footprint_mm2": footprint, "reorient_could_help": reorient_hint,
            "detail": "Part must fit the usable bed with +Z up; split, scale, or reorient."}


if __name__ == "__main__":
    import sys
    import json
    from geometry_io import load_mesh, sanitize
    from fdm_rules import load_profile
    m, _ = sanitize(load_mesh(sys.argv[1]))
    prof = load_profile(sys.argv[2] if len(sys.argv) > 2 else "generic")
    print(json.dumps(check_build_volume(m, prof["bed_mm"], prof["usable_margin_mm"]), indent=2))
