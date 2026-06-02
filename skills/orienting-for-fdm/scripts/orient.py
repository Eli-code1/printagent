"""Choose a print orientation for an FDM part, with no dependencies beyond trimesh
and numpy.

The method is the standard auto-orient heuristic: a good resting orientation lays
some face of the part's convex hull flat on the bed, so the candidates are exactly
those hull-face-down orientations. Each candidate is scored by the area that would
overhang past the printer's safe angle, the bed-contact area (adhesion), and the
height (shorter prints faster and is more stable). If a principal load direction is
given, orientations that put that load across the layers (the weak direction) are
penalised. The lowest-scoring candidate wins.

This picks an orientation; it does not slice. It composes only trimesh and numpy.

Usage:
    python orient.py PART.stl [--max-overhang 45] [--load X,Y,Z] [--out oriented.stl]
"""
from __future__ import annotations
import argparse
import json
import sys
import numpy as np
import trimesh


def _candidate_normals(mesh, max_candidates=40):
    """Unique outward normals of the convex hull, heaviest (largest area) first."""
    hull = mesh.convex_hull
    normals = np.asarray(hull.face_normals)
    areas = np.asarray(hull.area_faces)
    kept = []  # list of [normal, area]
    for n, a in zip(normals, areas):
        for k in kept:
            if np.dot(k[0], n) > 0.999:          # merge near-coplanar facets
                k[1] += a
                break
        else:
            kept.append([n / (np.linalg.norm(n) + 1e-12), a])
    kept.sort(key=lambda k: -k[1])
    return [k[0] for k in kept[:max_candidates]]


def _score(mesh, max_overhang_deg, load_dir=None):
    """Metrics for an already-oriented mesh (build direction is +Z)."""
    fn = mesh.face_normals
    areas = mesh.area_faces
    nz = fn[:, 2]
    diag = float(np.linalg.norm(mesh.extents)) or 1.0
    cz = mesh.triangles_center[:, 2]
    on_bed = cz <= mesh.bounds[0][2] + max(1e-3, 1e-4 * diag)
    down = nz < -1e-6
    oh_deg = np.degrees(np.arcsin(np.clip(np.abs(nz), 0.0, 1.0)))
    overhang_area = float(areas[down & ~on_bed & (oh_deg > max_overhang_deg)].sum())
    bed_area = float(areas[down & on_bed].sum())
    height = float(mesh.extents[2])
    total = float(mesh.area) or 1.0

    load_pen = 0.0
    if load_dir is not None:
        ld = np.asarray(load_dir, float)
        if np.linalg.norm(ld) > 1e-9:
            ld = ld / np.linalg.norm(ld)
            load_pen = 0.5 * abs(float(ld[2]))     # load along +Z = across layers = weak
    score = (overhang_area / total) - 0.4 * (bed_area / total) + 0.15 * (height / diag) + load_pen
    return {"score": round(score, 4),
            "overhang_area_mm2": round(overhang_area, 1),
            "bed_contact_mm2": round(bed_area, 1),
            "height_mm": round(height, 1)}


def pick_orientation(mesh, max_overhang_deg=45.0, load_dir=None):
    ranked = []
    for n in _candidate_normals(mesh):
        T = trimesh.geometry.align_vectors(n, [0.0, 0.0, -1.0])   # rest face n on bed
        m = mesh.copy()
        m.apply_transform(T)
        m.apply_translation([0, 0, -m.bounds[0][2]])              # drop onto z = 0
        ld = (T[:3, :3] @ np.asarray(load_dir, float)) if load_dir is not None else None
        s = _score(m, max_overhang_deg, ld)
        euler = np.degrees(trimesh.transformations.euler_from_matrix(T, "sxyz"))
        ranked.append({**s, "euler_deg": [round(float(e), 1) for e in euler],
                       "matrix": [[round(float(v), 6) for v in row] for row in T]})
    ranked.sort(key=lambda r: r["score"])
    return ranked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("part")
    ap.add_argument("--max-overhang", type=float, default=45.0)
    ap.add_argument("--load", default=None, help="principal load direction, e.g. 0,0,1")
    ap.add_argument("--out", default=None, help="write the best-oriented STL here")
    a = ap.parse_args()
    load = [float(x) for x in a.load.split(",")] if a.load else None
    mesh = trimesh.load(a.part, force="mesh")
    ranked = pick_orientation(mesh, a.max_overhang, load)
    best = ranked[0]
    if a.out:
        m = mesh.copy()
        m.apply_transform(np.array(best["matrix"]))
        m.apply_translation([0, 0, -m.bounds[0][2]])
        m.export(a.out)
    print(json.dumps({"best": best, "alternatives": ranked[1:5],
                      "candidates_evaluated": len(ranked)}, indent=2))


if __name__ == "__main__":
    main()
