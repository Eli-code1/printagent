"""Load and sanitize geometry for the manufacturability gates.

Returns a trimesh.Trimesh (always) and, when the source is B-rep (STEP/BREP),
an optional OCCT TopoDS_Shape for exact checks. Executed or imported.
"""
from __future__ import annotations
import os
import tempfile
import trimesh


def load_mesh(path: str) -> trimesh.Trimesh:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".step", ".stp", ".brep"):
        return _mesh_from_brep(path, ext)
    loaded = trimesh.load(path, force="mesh")
    if isinstance(loaded, trimesh.Trimesh):
        return loaded
    return loaded.dump(concatenate=True)  # Scene -> single mesh


def _mesh_from_brep(path: str, ext: str) -> trimesh.Trimesh:
    """Tessellate a B-rep via build123d, round-tripping through a temp STL."""
    from build123d import import_step, import_brep, export_stl
    obj = import_step(path) if ext in (".step", ".stp") else import_brep(path)
    fd, tmp = tempfile.mkstemp(suffix=".stl")
    os.close(fd)
    try:
        export_stl(obj, tmp, tolerance=0.01, angular_tolerance=0.1)
        return trimesh.load(tmp, force="mesh")
    finally:
        os.unlink(tmp)


def sanitize(mesh: trimesh.Trimesh) -> tuple[trimesh.Trimesh, dict]:
    """Repair what is safely repairable; report health. Never silently hides a
    non-watertight mesh, downstream volume/inertia would be meaningless."""
    mesh.merge_vertices()
    mesh.process(validate=True)   # dedupe faces/vertices, drop degenerate
    mesh.fix_normals()
    if not mesh.is_watertight:
        mesh.fill_holes()
    health = {
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "euler_number": int(mesh.euler_number),
        "volume_mm3": float(mesh.volume) if mesh.is_watertight else None,
        "n_faces": int(len(mesh.faces)),
    }
    return mesh, health


def load_shape(path: str):
    """Optional OCCT TopoDS_Shape for B-rep-exact checks; None for meshes."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".step", ".stp", ".brep"):
        return None
    try:
        from build123d import import_step, import_brep
        obj = import_step(path) if ext in (".step", ".stp") else import_brep(path)
        return obj.wrapped  # TopoDS_Shape
    except Exception:
        return None
