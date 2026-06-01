"""Cheap pre-gate: check a built part against its PartSpec invariants BEFORE the
expensive DFM gate runs. Every check is closed-form via trimesh (bounding box,
volume, disjoint-solid count, through-hole count by genus, watertightness, and a
planar bottom), so it runs in well under a second and filters out obviously-wrong
generations before any heavy work. A failed invariant becomes a concrete fix-list
entry the generator can act on.

Usage:
    python run_invariants.py PART.stl spec.json
where spec.json is a PartSpec dict (its "invariants" block is read) or an
invariants dict on its own.
"""
from __future__ import annotations
import json
import sys
import numpy as np
import trimesh


def _genus_holes(mesh):
    """Through-hole count for a single watertight body is the genus, 1 - euler/2."""
    try:
        return max(0, int(round(1 - mesh.euler_number / 2.0)))
    except Exception:
        return None


def _has_planar_bottom(mesh, tol_deg=5.0):
    zmin = mesh.bounds[0][2]
    diag = float(np.linalg.norm(mesh.extents)) or 1.0
    down = mesh.face_normals[:, 2] < -np.cos(np.radians(tol_deg))
    on_floor = mesh.triangles_center[:, 2] <= zmin + max(1e-3, 1e-4 * diag)
    return bool(float(mesh.area_faces[down & on_floor].sum()) > 1e-6)


def check_invariants(mesh, inv: dict, present_features=None):
    checks, fixes = [], []

    def rec(name, ok, expected, actual, hint):
        checks.append({"name": name, "ok": bool(ok), "expected": expected, "actual": actual})
        if not ok:
            fixes.append({"invariant": name, "expected": expected, "actual": actual,
                          "hint": hint})

    wt = bool(mesh.is_watertight)
    if inv.get("watertight", True):
        rec("watertight", wt, True, wt,
            "close the mesh; boolean artifacts or zero-thickness faces leave it open")

    ext = [round(float(x), 3) for x in mesh.extents]
    if inv.get("bbox_min_mm") or inv.get("bbox_max_mm"):
        lo = inv.get("bbox_min_mm") or [0.0, 0.0, 0.0]
        hi = inv.get("bbox_max_mm") or [1e9, 1e9, 1e9]
        ok = all(lo[i] - 1e-6 <= ext[i] <= hi[i] + 1e-6 for i in range(3))
        rec("bbox_mm", ok, {"min": lo, "max": hi}, ext,
            "scale or re-dimension so the bounding box lands in range")

    if inv.get("volume_mm3") is not None:
        tol, exp = inv.get("volume_tol", 0.30), inv["volume_mm3"]
        actual = round(float(mesh.volume), 2) if wt else None
        ok = actual is not None and abs(actual - exp) <= tol * exp
        rec("volume_mm3", ok, {"target": exp, "tol": tol}, actual,
            "volume off target; check wall thickness, infill solids, or missing/extra bodies")

    if inv.get("solid_count") is not None:
        bodies = len(mesh.split(only_watertight=False))
        rec("solid_count", bodies == inv["solid_count"], inv["solid_count"], bodies,
            "merge stray bodies or union the part into one solid")

    if inv.get("hole_count") is not None:
        holes = _genus_holes(mesh)
        rec("hole_count", holes == inv["hole_count"], inv["hole_count"], holes,
            "add or remove through holes to match the spec")

    if inv.get("planar_bottom") is not None:
        pb = _has_planar_bottom(mesh)
        rec("planar_bottom", pb == bool(inv["planar_bottom"]), bool(inv["planar_bottom"]), pb,
            "add a flat base on the build plane for bed adhesion")

    want = inv.get("named_features") or []
    if want:
        if present_features is None:
            checks.append({"name": "named_features", "ok": None, "expected": want,
                           "actual": "not checkable from the mesh alone"})
        else:
            missing = [f for f in want if f not in present_features]
            rec("named_features", not missing, want, present_features,
                f"missing features: {missing}")

    passed = all(c["ok"] for c in checks if c["ok"] is not None)
    return {"name": "invariants", "passed": passed, "checks": checks, "fixes": fixes}


if __name__ == "__main__":
    mesh = trimesh.load(sys.argv[1], force="mesh")
    data = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
    inv = data.get("invariants", data) or {}
    res = check_invariants(mesh, inv)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["passed"] else 1)
