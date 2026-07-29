"""Enclosed-volume gate. Flood-fills empty space from the bounding-box boundary;
any empty region unreachable from outside is a sealed cavity that cannot drain.
Hard fail. Remedy: add a >=3 mm vent at the reported centroid."""
from __future__ import annotations
import numpy as np
from scipy import ndimage


def check_enclosed_volumes(mesh, pitch=0.5, min_void_mm3=1.0, max_voxels=40_000_000):
    note = None
    est = float(np.prod(np.ceil(mesh.extents / pitch) + 2))
    if est > max_voxels:
        pitch = float((float(np.prod(mesh.extents)) / max_voxels) ** (1 / 3))
        note = (f"pitch increased to {pitch:.3f} mm to fit budget; "
                f"drains smaller than ~{pitch:.2f} mm may be falsely sealed")

    try:
        vg = mesh.voxelized(pitch=pitch).fill()
    except Exception:
        # The default subdivide-based voxelizer hits subdivide_to_size
        # max_iter on large parts; the ray voxelizer needs no subdivision.
        vg = mesh.voxelized(pitch=pitch, method="ray").fill()
        note = ((note + "; ") if note else "") + "ray voxelizer fallback"
    solid = np.pad(vg.matrix, 1, mode="constant", constant_values=False)
    labels, n = ndimage.label(~solid)             # label empty space

    faces = [labels[0], labels[-1], labels[:, 0], labels[:, -1],
             labels[:, :, 0], labels[:, :, -1]]
    outside = set(np.unique(np.concatenate([f.ravel() for f in faces])))
    outside.discard(0)

    voids, vox_vol = [], pitch ** 3
    for lab in range(1, n + 1):
        if lab in outside:
            continue
        vol = int((labels == lab).sum()) * vox_vol
        if vol < min_void_mm3:
            continue
        centroid = None
        try:
            idx = np.argwhere(labels == lab) - 1   # undo pad
            centroid = [round(float(v), 1) for v in vg.indices_to_points(idx).mean(0)]
        except Exception:
            pass
        voids.append({"volume_mm3": round(vol, 2), "centroid_mm": centroid})

    out = {"name": "enclosed_volumes", "passed": bool(len(voids) == 0),
           "severity": "fail", "pitch_mm": round(pitch, 3), "enclosed_voids": voids,
           "detail": "Sealed cavities trap support/moisture and prevent drainage; add a vent."}
    if note:
        out["warning"] = note
    return out


if __name__ == "__main__":
    import sys
    import json
    from geometry_io import load_mesh, sanitize
    m, _ = sanitize(load_mesh(sys.argv[1]))
    print(json.dumps(check_enclosed_volumes(m), indent=2))
