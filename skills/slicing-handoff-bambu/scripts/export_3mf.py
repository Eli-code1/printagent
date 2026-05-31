"""Export a part to millimetre 3MF (slicer-facing) and ensure a STEP archive exists."""
from __future__ import annotations
import os
import shutil

from geometry_io import load_mesh


def export_3mf(src_path: str, out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    mesh = load_mesh(src_path)
    mesh.merge_vertices()
    mesh.process(validate=True)
    mesh.fix_normals()

    three_mf = os.path.join(out_dir, "model.3mf")
    mesh.export(three_mf)            # trimesh writes 3MF (mm by convention)

    step_out = os.path.join(out_dir, "model.step")
    if src_path.lower().endswith((".step", ".stp")):
        shutil.copyfile(src_path, step_out)
    else:
        try:                          # re-derive STEP from the original if it was a B-rep
            from build123d import import_step, export_step
            export_step(import_step(src_path), step_out)
        except Exception:
            step_out = None           # mesh source: no lossless STEP available
    return {"model_3mf": three_mf, "model_step": step_out,
            "bbox_mm": [round(float(v), 2) for v in mesh.extents],
            "watertight": bool(mesh.is_watertight), "n_faces": int(len(mesh.faces))}
