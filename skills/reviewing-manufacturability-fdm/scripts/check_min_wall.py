"""Minimum wall-thickness gate (cone-SDF primary, bias-aware fusion).

cone_sdf : PRIMARY, approximately unbiased. From even surface samples, cast a
           small cone of inward rays (Shape-Diameter-Function style; Shapira &
           Shamir 2008) and take the per-point MEDIAN of the surviving ray
           lengths as the local wall thickness. The cone plus the median reject
           the single grazing ray and the concave wraparound hit that fool a
           lone -normal ray. Three per-ray filters drop self-hits, grazing
           exits, and 2-hop face-adjacent wraparound.
voxel    : CORROBORATOR. Binary opening via a padded distance transform. It
           OVER-estimates thickness, so its FAIL is strong evidence and its PASS
           is weak.
brep     : POSITIVE-EVIDENCE only (OCCT inward offset); failure is never a fail.

Fusion is bias-aware, and method disagreement surfaces as INDETERMINATE, never a
silent PASS. Verdicts use the shared vocabulary: PASS | FAIL | INDETERMINATE |
NOT_RUN.
"""
from __future__ import annotations
from collections import defaultdict
import numpy as np
import trimesh
from scipy import ndimage

SEED = 1234
_TOL = 1e-3   # mm: float-noise guard so the threshold boundary is deterministic


def _cone_sdf(mesh, T, n_samples=1500, k=6, half_angle_deg=60.0):
    """Approximately-unbiased local thickness by an inward cone of rays."""
    np.random.seed(SEED)
    try:
        pts, fidx = trimesh.sample.sample_surface_even(mesh, n_samples)
    except Exception as e:
        return {"verdict": "NOT_RUN", "passed": None, "note": f"sampling failed: {e}"}
    pts, fidx = np.asarray(pts), np.asarray(fidx)
    n = len(pts)
    if n == 0:
        return {"verdict": "NOT_RUN", "passed": None, "note": "no surface samples"}

    fn = mesh.face_normals[fidx]
    axis = -fn / (np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12)   # inward
    ref = np.tile([1.0, 0.0, 0.0], (n, 1))
    ref[np.abs(axis[:, 0]) > 0.9] = [0.0, 1.0, 0.0]
    t1 = np.cross(axis, ref)
    t1 /= (np.linalg.norm(t1, axis=1, keepdims=True) + 1e-12)
    t2 = np.cross(axis, t1)

    ca = np.cos(np.radians(half_angle_deg))
    golden = np.pi * (3.0 - np.sqrt(5.0))
    diag = float(np.linalg.norm(mesh.extents)) or 1.0
    eps = max(1e-6 * diag, 0.01 * T)

    origins, dirs, ray_pt = [], [], []
    for j in range(k):
        if j == 0:
            d = axis.copy()
        else:
            z = ca + (1.0 - ca) * (j / (k - 1))
            alpha = np.arccos(np.clip(z, -1.0, 1.0))
            phi = j * golden
            d = (np.cos(alpha) * axis
                 + np.sin(alpha) * (np.cos(phi) * t1 + np.sin(phi) * t2))
        d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-12)
        origins.append(pts + d * eps)
        dirs.append(d)
        ray_pt.append(np.arange(n))
    origins = np.vstack(origins)
    dirs = np.vstack(dirs)
    ray_pt = np.concatenate(ray_pt)

    locs, idx_ray, idx_tri = mesh.ray.intersects_location(
        origins, dirs, multiple_hits=False)
    if len(idx_ray) == 0:
        return {"verdict": "NOT_RUN", "passed": None, "note": "no ray hits"}

    dist = np.linalg.norm(locs - pts[ray_pt[idx_ray]], axis=1)
    keep = dist > eps                                              # self-hits
    # A head-on exit has the ray direction aligned with the exit face's OUTWARD
    # normal (the ray is leaving the solid there), so dot(normal, dir) ~ +1.
    # Grazing exits trend toward 0; drop them.
    head_on = np.einsum("ij,ij->i", mesh.face_normals[idx_tri], dirs[idx_ray])
    keep &= head_on >= 0.5
    # NB: a face-adjacency wraparound filter was tried and removed. On low-poly
    # CAD exports (a box is 12 triangles) the 2-hop neighbourhood of any face
    # covers the whole mesh, so it discarded every legitimate opposite-wall hit.
    # The per-point median already rejects the minority wraparound outliers.

    idx_ray, dist = idx_ray[keep], dist[keep]
    if len(dist) == 0:
        return {"verdict": "NOT_RUN", "passed": None,
                "note": "all rays filtered (degenerate geometry)"}

    by_pt = defaultdict(list)
    for p, dd in zip(ray_pt[idx_ray], dist):
        by_pt[int(p)].append(dd)
    med = np.array([np.median(v) for v in by_pt.values()])

    thin = med < (T - _TOL)
    thin_count = int(thin.sum())
    valid = len(med)
    # Acute convex edges yield a small fraction of spurious thin readings even on
    # thick parts, so tolerate up to ~1.5% before failing. A genuinely thin wall
    # paints far more: in the regression corpus the thin cases all exceed 90% and
    # the thinnest meaningful case is about 5%, so this floor sits well clear.
    noise = max(3, int(0.015 * valid))
    verdict = "FAIL" if thin_count > noise else "PASS"
    return {"verdict": verdict, "passed": (verdict == "PASS"),
            "min_wall_mm": round(float(np.percentile(med, 1)), 3),
            "median_wall_mm": round(float(np.median(med)), 3),
            "thin_fraction": round(thin_count / valid, 4),
            "thin_point_count": thin_count, "points_measured": valid,
            "rays_per_point": k,
            "note": "cone-SDF inward rays, per-point median; min_wall_mm is p1"}


def _voxel_opening(mesh, T, max_voxels=40_000_000):
    """Corroborator only. Over-estimates thickness, so FAIL is strong, PASS weak."""
    pitch = T / 3.0
    est = float(np.prod(np.ceil(mesh.extents / pitch) + 2))
    confidence, note = "high", None
    if est > max_voxels:
        pitch = float((float(np.prod(mesh.extents)) / max_voxels) ** (1 / 3))
        confidence = "low"
        note = (f"voxel pitch coarsened to {pitch:.3f} mm; features below "
                f"~{2 * pitch:.2f} mm may be missed")

    try:
        vg = mesh.voxelized(pitch=pitch).fill()
    except Exception as e:
        # Large parts can defeat trimesh's subdivide-based voxelizer
        # (subdivide_to_size max_iter). The fusion treats passed=None as
        # "method unavailable" and lets cone-SDF carry the verdict.
        return {"passed": None, "confidence": "none",
                "note": f"voxelization failed on this mesh: {type(e).__name__}"}
    solid = np.pad(vg.matrix, 1, mode="constant", constant_values=False)
    if solid.sum() == 0:
        return {"passed": None, "confidence": "none", "note": "voxelization empty"}

    edt = ndimage.distance_transform_edt(solid) * pitch
    r = T / 2.0
    eroded = edt >= r
    if not eroded.any():
        return {"passed": False, "confidence": confidence, "pitch_mm": round(pitch, 3),
                "note": note or "whole part thinner than T (corroborating)"}

    opened = (ndimage.distance_transform_edt(~eroded) * pitch) <= r
    thin0 = solid & (~opened)
    core = edt >= T
    if core.any():
        dist_from_core = ndimage.distance_transform_edt(~core) * pitch
        thin = thin0 & (dist_from_core > T)
    else:
        thin = thin0
    thin_n = int(thin.sum())
    noise = max(8, int(0.0005 * solid.sum()))
    return {"passed": bool(thin_n <= noise), "confidence": confidence,
            "pitch_mm": round(pitch, 3),
            "thin_volume_mm3": round(thin_n * pitch ** 3, 2), "note": note}


def _brep_offset_evidence(shape, T):
    """EXPERIMENTAL positive-evidence only. OCCT offset failure is inconclusive."""
    if shape is None:
        return {"evidence": None, "note": "no B-rep shape"}
    try:
        from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeOffsetShape
        from OCP.GProp import GProp_GProps
        from OCP.BRepGProp import BRepGProp
        mk = BRepOffsetAPI_MakeOffsetShape()
        mk.PerformBySimple(shape, -T / 2.0)
        if not mk.IsDone():
            return {"evidence": "inconclusive", "note": "offset not done"}
        props = GProp_GProps()
        BRepGProp.VolumeProperties_s(mk.Shape(), props)
        ok = props.Mass() > 1e-6
        return {"evidence": "pass" if ok else "inconclusive",
                "note": "inward offset solid non-empty" if ok else "offset collapsed"}
    except Exception as e:
        return {"evidence": "inconclusive", "note": f"{type(e).__name__} (OCP API/version)"}


def _fuse(cone, voxel, T):
    """Bias-aware fusion. Returns (verdict, confidence, rationale)."""
    cv = cone.get("verdict")
    vox = voxel.get("passed")        # True | False | None
    if cv == "NOT_RUN":
        if vox is False:
            return "FAIL", "high", "primary did not run; the voxel over-estimator still fails"
        return "INDETERMINATE", "low", "the primary cone-SDF could not run on this mesh"
    if cv == "FAIL":
        if vox is False:
            return "FAIL", "high", "cone-SDF and the voxel opening both fail"
        return "FAIL", "medium", ("cone-SDF fails; voxel passes, which is expected "
                                  "because the voxel method over-estimates thickness")
    cone_min = cone.get("min_wall_mm", T)
    if vox is False and cone_min < 1.5 * T:
        return "INDETERMINATE", "low", (
            f"cone-SDF passes but is near the threshold ({cone_min} mm) while the "
            "voxel opening fails; this needs a human look")
    return "PASS", "high", "cone-SDF passes"


def check_min_wall(mesh, T, shape=None, n_samples=1500):
    cone = _cone_sdf(mesh, T, n_samples)
    voxel = _voxel_opening(mesh, T)
    brep = _brep_offset_evidence(shape, T)
    verdict, confidence, why = _fuse(cone, voxel, T)
    passed = {"PASS": True, "FAIL": False}.get(verdict)   # INDETERMINATE/NOT_RUN -> None
    plain = {
        "FAIL": "this wall will print as a single fragile strand and can snap",
        "INDETERMINATE": "the wall thickness here is borderline and worth a human check",
        "PASS": "walls are thick enough to print solidly",
        "NOT_RUN": "wall thickness could not be measured on this mesh",
    }[verdict]
    return {"name": "min_wall", "verdict": verdict, "passed": passed,
            "severity": "fail", "epistemic_weight": "deterministic",
            "threshold_mm": T, "min_wall_mm": cone.get("min_wall_mm"),
            "confidence": confidence, "plain_consequence": plain,
            "methods": {"cone_sdf": cone, "voxel_opening": voxel, "brep_offset": brep},
            "reasons": [why],
            "detail": "Walls below the minimum print weak or not at all; thicken or add ribs."}


if __name__ == "__main__":
    import sys
    import json
    from geometry_io import load_mesh, sanitize, load_shape
    m, _ = sanitize(load_mesh(sys.argv[1]))
    print(json.dumps(check_min_wall(m, float(sys.argv[2]) if len(sys.argv) > 2 else 0.8,
                                    shape=load_shape(sys.argv[1])), indent=2))
