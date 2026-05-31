"""Compact loader for the structural reviewer. Self-contained copy."""
from __future__ import annotations
import os
import tempfile
import trimesh


def load_mesh(path: str) -> trimesh.Trimesh:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".step", ".stp", ".brep"):
        from build123d import import_step, import_brep, export_stl
        obj = import_step(path) if ext in (".step", ".stp") else import_brep(path)
        fd, tmp = tempfile.mkstemp(suffix=".stl")
        os.close(fd)
        try:
            export_stl(obj, tmp, tolerance=0.01, angular_tolerance=0.1)
            return trimesh.load(tmp, force="mesh")
        finally:
            os.unlink(tmp)
    loaded = trimesh.load(path, force="mesh")
    return loaded if isinstance(loaded, trimesh.Trimesh) else loaded.dump(concatenate=True)


def sanitize(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    mesh.merge_vertices()
    mesh.process(validate=True)
    mesh.fix_normals()
    if not mesh.is_watertight:
        mesh.fill_holes()
    return mesh
