"""Minimum wall-thickness gate.

ray thickness : AUTHORITATIVE. From even surface samples, cast a ray inward
                along the -normal to the opposite wall; that distance IS the
                local wall thickness. Unlike max_sphere it does NOT collapse at
                convex edges (a solid cube reads its full width everywhere), so
                no corner/edge-exclusion heuristics are needed. A part fails
                when a meaningful fraction of the sampled surface is thinner
                than T (a few spurious grazing rays are tolerated).
voxel opening : CORROBORATING evidence only, never the verdict. trimesh's
                voxelized().fill() over-thickens thin features by ~1-2 cells,
                so the ball-fit test can miss genuinely thin walls.
brep offset   : EXPERIMENTAL positive-evidence only; failure is never a fail.
"""
from __future__ import annotations
import numpy as np
import trimesh
from scipy import ndimage


def _ray_thickness(mesh, T, n_samples=4000):
    """Authoritative wall-thickness gate by inward ray casting."""
    from trimesh.proximity import thickness
    try:
        pts, _ = trimesh.sample.sample_surface_even(mesh, n_samples)
    except Exception as e:
        return {"passed": None, "confidence": "none", "note": f"sampling failed: {e}"}
    if len(pts) == 0:
        return {"passed": None, "confidence": "none", "note": "no surface samples"}

    th = thickness(mesh=mesh, points=pts, exterior=False, method="ray")
    valid = np.isfinite(th) & (th > 1e-6)
    th, pts = th[valid], pts[valid]
    if len(th) == 0:
        return {"passed": None, "confidence": "none", "note": "no valid thickness rays"}

    thin = th < T
    thin_count = int(thin.sum())
    # Tolerate a few spurious grazing/edge rays; a genuine thin wall paints many
    # samples. Floor is the larger of 3 rays or 0.2% of the sampled surface.
    noise = max(3, int(0.002 * len(th)))
    passed = bool(thin_count <= noise)

    locs = []
    if not passed:
        tp = pts[thin]
        step = max(1, len(tp) // 8)
        for p in tp[::step][:8]:
            locs.append([round(float(v), 1) for v in p])

    return {"passed": passed, "confidence": "high",
            "min_wall_mm": round(float(np.percentile(th, 1)), 3),
            "raw_min_mm": round(float(th.min()), 3),
            "thin_area_fraction": round(thin_count / len(th), 4),
            "thin_sample_count": thin_count, "samples": int(len(th)),
            "thin_locations_mm": locs,
            "note": "inward ray-cast normal thickness; min_wall_mm is the robust p1"}


def _voxel_opening(mesh, T, max_voxels=40_000_000):
    """Corroborating only. NOT authoritative — see module docstring."""
    pitch = T / 3.0
    est = float(np.prod(np.ceil(mesh.extents / pitch) + 2))
    confidence, note = "high", None
    if est > max_voxels:
        pitch = float((float(np.prod(mesh.extents)) / max_voxels) ** (1 / 3))
        confidence = "low"
        note = (f"voxel pitch coarsened to {pitch:.3f} mm to fit budget; "
                f"features below ~{2 * pitch:.2f} mm may be missed")

    vg = mesh.voxelized(pitch=pitch).fill()
    # Pad with a background shell so the distance transform has an exterior to
    # measure against; without it a bbox-filling solid yields a garbage EDT.
    solid = np.pad(vg.matrix, 1, mode="constant", constant_values=False)
    if solid.sum() == 0:
        return {"passed": None, "confidence": "none", "note": "voxelization empty"}

    edt = ndimage.distance_transform_edt(solid) * pitch       # mm to surface
    r = T / 2.0
    eroded = edt >= r                                         # ball-center voxels
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
    """EXPERIMENTAL. Inward offset of T/2; success => weak evidence walls >= T.
    OCCT offset is fragile and version-sensitive — failure is always inconclusive."""
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
        return {"evidence": "inconclusive", "note": f"{type(e).__name__} (check OCP API/version)"}


def check_min_wall(mesh, T, shape=None, n_samples=4000):
    ray = _ray_thickness(mesh, T, n_samples)
    voxel = _voxel_opening(mesh, T)        # corroboration only
    brep = _brep_offset_evidence(shape, T)

    # Ray-cast normal thickness is the sole pass/fail authority. The voxel
    # opening over-thickens thin features and max_sphere collapses at convex
    # edges, so neither can be trusted as the verdict.
    passed = ray.get("passed")
    reasons = []
    if passed is False:
        reasons.append(f"ray thickness: {ray.get('thin_area_fraction')} of the sampled "
                       f"surface is thinner than {T} mm (min ~{ray.get('min_wall_mm')} mm)")
    elif passed is None:
        reasons.append(f"inconclusive: {ray.get('note')}")

    return {"name": "min_wall", "passed": passed, "severity": "fail",
            "threshold_mm": T, "min_wall_mm": ray.get("min_wall_mm"),
            "confidence": ray.get("confidence", "unknown"),
            "methods": {"ray_thickness": ray, "voxel_opening": voxel,
                        "brep_offset": brep},
            "reasons": reasons,
            "detail": "Walls below the minimum print weak or not at all; thicken or add ribs."}


if __name__ == "__main__":
    import sys
    import json
    from geometry_io import load_mesh, sanitize, load_shape
    m, _ = sanitize(load_mesh(sys.argv[1]))
    print(json.dumps(check_min_wall(m, float(sys.argv[2]) if len(sys.argv) > 2 else 0.8,
                                    shape=load_shape(sys.argv[1])), indent=2))
