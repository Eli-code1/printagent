"""Loop glue: build a part from a build123d script, export it, run the manufacturability
gate, and emit a combined result whose fix_list names the exact edit for each failure.

Usage:
    python build_and_check.py my_part.py --printer bambu_x1c --profile structural \
        --gate-dir ../reviewing-manufacturability-fdm/scripts

`my_part.py` must define a module-level `part` (a build123d object) or `build()` returning one.
Exit code 0 = manufacturable, 1 = not.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import os
import sys

from export_part import export_part


def load_part(script_path: str):
    spec = importlib.util.spec_from_file_location("user_part", script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    part = getattr(mod, "part", None)
    if part is None and hasattr(mod, "build"):
        part = mod.build()
    if part is None:
        raise SystemExit("script must define a module-level `part` or a build() function")
    return part


def to_fix_list(report: dict) -> list[str]:
    fixes: list[str] = []
    for g in report.get("gates", []):
        if g.get("passed") is True:
            continue
        name = g.get("name")
        if name == "watertight":
            fixes.append("Not watertight: make the result a single closed solid; check for "
                         "a boolean leaving a sliver or coincident face.")
        elif name == "min_wall":
            locs = g.get("methods", {}).get("voxel_opening", {}).get("thin_locations_mm")
            fixes.append(f"Thicken to >= {g.get('threshold_mm')} mm (min measured "
                         f"{g.get('min_wall_mm')}). Use shell(part, t) with larger t or add "
                         f"ribs. Thin regions near {locs}.")
        elif name == "overhangs":
            fixes.append(f"Overhang up to {g.get('worst_overhang_deg')} deg over "
                         f"{g.get('overhanging_area_mm2')} mm^2 beyond "
                         f"{g.get('threshold_deg_from_vertical')} deg: reorient the build, or "
                         f"chamfer_bottom_edges(part) / convert downward fillets to chamfers.")
        elif name == "enclosed_volumes":
            for v in g.get("enclosed_voids", []):
                fixes.append(f"Sealed void {v['volume_mm3']} mm^3 at {v['centroid_mm']}: "
                             f"add_vent(part, {v['centroid_mm']}, 3.0).")
        elif name == "build_volume":
            tail = (" or reorient (OBB fits)." if g.get("reorient_could_help")
                    else ", split or scale.")
            fixes.append(f"Part {g.get('aabb_extents_mm')} exceeds usable "
                         f"{g.get('usable_envelope_mm')}{tail}")
    return fixes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--printer", default="generic")
    ap.add_argument("--nozzle", type=float, default=0.4)
    ap.add_argument("--layer-height", type=float, default=0.2)
    ap.add_argument("--profile", choices=["cosmetic", "structural"], default="structural")
    ap.add_argument("--gate-dir", default="../reviewing-manufacturability-fdm/scripts")
    ap.add_argument("--stem", default="_part")
    a = ap.parse_args()

    part = load_part(a.script)
    step_path = export_part(part, a.stem)

    sys.path.insert(0, os.path.abspath(a.gate_dir))
    import run_checks  # provided by reviewing-manufacturability-fdm
    report = run_checks.run(step_path, a.printer, a.nozzle, a.layer_height, a.profile)

    report["fix_list"] = to_fix_list(report)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["manufacturable"] else 1)


if __name__ == "__main__":
    main()
