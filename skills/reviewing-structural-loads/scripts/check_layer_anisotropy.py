"""Load direction vs layer plane, plus weakest cross-section along the build axis."""
from __future__ import annotations
import numpy as np


def check_layer_anisotropy(mesh, load_dir=(0, 0, 1), build_dir=(0, 0, 1),
                           z_factor_lo=0.4, z_factor_hi=0.7, n_slices=40):
    ld = np.asarray(load_dir, float)
    if np.linalg.norm(ld) < 1e-9:
        across = 0.0
    else:
        bz = np.asarray(build_dir, float)
        bz /= np.linalg.norm(bz)
        across = float(abs((ld / np.linalg.norm(ld)) @ bz))   # 0=in-plane, 1=pure Z

    # weakest cross-section scan along build axis
    zmin, zmax = float(mesh.bounds[0, 2]), float(mesh.bounds[1, 2])
    zs = np.linspace(zmin + 1e-3, zmax - 1e-3, n_slices)
    areas = []
    for z in zs:
        try:
            sec = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
            if sec is None:
                continue
            p2d, _ = sec.to_planar()
            areas.append((float(z), float(sum(p.area for p in p2d.polygons_full))))
        except Exception:
            continue
    weakest = min(areas, key=lambda t: t[1]) if areas else (None, None)

    warnings = []
    if across > 0.5:
        warnings.append(f"principal load is {round(across*100)}% across layer lines; "
                        f"Z strength is ~{z_factor_lo}-{z_factor_hi}x of XY. Reorient so the "
                        f"load sits in the XY plane, or accept reduced strength.")
    return {"name": "layer_anisotropy",
            "passed": bool(across <= 0.5),
            "severity": "warning",
            "load_fraction_across_layers": round(across, 2),
            "weakest_section_mm2": (round(weakest[1], 1) if weakest[1] else None),
            "weakest_section_z_mm": (round(weakest[0], 1) if weakest[0] else None),
            "warnings": warnings,
            "detail": "Tension across layer lines is the dominant FDM failure mode."}
