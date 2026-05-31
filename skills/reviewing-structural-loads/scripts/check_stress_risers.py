"""Sharp concave (reentrant) edges concentrate stress; flag them and recommend a fillet."""
from __future__ import annotations
import numpy as np


def check_stress_risers(mesh, sharp_angle_deg=50.0, min_total_length_mm=2.0):
    try:
        angles = np.degrees(mesh.face_adjacency_angles)     # between adjacent face normals
        convex = mesh.face_adjacency_convex                 # True if convex edge
        edges = mesh.face_adjacency_edges                   # shared edge vertex indices
    except Exception:
        return {"name": "stress_risers", "passed": None,
                "detail": "face adjacency unavailable on this mesh"}

    sharp_concave = (~convex) & (angles > sharp_angle_deg)
    v = mesh.vertices
    seg = edges[sharp_concave]
    if len(seg) == 0:
        return {"name": "stress_risers", "passed": True, "severity": "warning",
                "sharp_concave_edges": 0, "detail": "no sharp internal corners found"}
    lengths = np.linalg.norm(v[seg[:, 0]] - v[seg[:, 1]], axis=1)
    total = float(lengths.sum())
    mids = (v[seg[:, 0]] + v[seg[:, 1]]) / 2.0
    locs = [[round(float(c), 1) for c in m] for m in mids[np.argsort(-lengths)[:6]]]
    return {"name": "stress_risers",
            "passed": bool(total < min_total_length_mm),
            "severity": "warning",
            "sharp_concave_edges": int(len(seg)),
            "total_length_mm": round(total, 1),
            "sample_locations_mm": locs,
            "recommended_fillet_mm": 1.0,
            "detail": "Fillet sharp internal corners (>= ~1 mm) to relieve stress concentration."}
