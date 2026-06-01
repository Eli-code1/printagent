"""Orchestrator. Runs every manufacturability gate and emits verification.json.

Usage:
    python run_checks.py PART_FILE --printer bambu_x1c --nozzle 0.4 \
        --layer-height 0.2 --profile structural

Exit code 0 = manufacturable, 1 = not. Full result prints as JSON to stdout.
"""
from __future__ import annotations
import argparse
import json
import sys

from geometry_io import load_mesh, sanitize, load_shape
from fdm_rules import resolve_thresholds, load_profile
from check_min_wall import check_min_wall
from check_overhangs import check_overhangs
from check_enclosed_volumes import check_enclosed_volumes
from check_build_volume import check_build_volume


def run(path, printer="generic", nozzle=0.4, layer_height=0.2, profile="structural"):
    mesh, health = sanitize(load_mesh(path))
    shape = load_shape(path)
    th = resolve_thresholds(nozzle, layer_height, profile, printer)
    prof = load_profile(printer)

    watertight_gate = {"name": "watertight", "severity": "fail",
                       "passed": health["watertight"],
                       "detail": "Non-watertight mesh; volume/inertia unreliable. Fix first."}
    gates = [
        watertight_gate,
        check_min_wall(mesh, th.min_wall, shape=shape),
        check_overhangs(mesh, th.max_overhang_deg),
        check_enclosed_volumes(mesh, min_void_mm3=th.enclosed_void_min_mm3),
        check_build_volume(mesh, prof["bed_mm"], prof["usable_margin_mm"]),
    ]

    gates = [_normalize(g) for g in gates]
    hard_fail = [g for g in gates if g.get("severity") == "fail" and g.get("passed") is False]
    soft = [g for g in gates if g.get("passed") is not True and g not in hard_fail]
    manufacturable = (len(hard_fail) == 0) and bool(health["watertight"])
    overall = "FAIL" if hard_fail else ("WARNING" if soft else "PASS")

    return {
        "part": path,
        "manufacturable": manufacturable,
        "overall_verdict": overall,
        "params": th.to_dict(),
        "printer": printer,
        "mesh_health": health,
        "gates": gates,
        "gates_passed": [g["name"] for g in gates if g.get("passed") is True],
        "gates_failed": [g["name"] for g in hard_fail],
        "warnings": [g["name"] for g in soft],
    }


def _normalize(g):
    """Ensure every gate carries the shared verdict vocabulary and an epistemic
    weight, so plain_report and downstream skills read one consistent schema.
    PASS | FAIL | WARNING | INDETERMINATE | NOT_RUN."""
    if "verdict" not in g:
        p = g.get("passed")
        g["verdict"] = ("PASS" if p is True else "INDETERMINATE" if p is None
                        else ("FAIL" if g.get("severity") == "fail" else "WARNING"))
    g.setdefault("epistemic_weight",
                 "deterministic" if g.get("severity") == "fail" else "heuristic_advisory")
    return g


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("part")
    ap.add_argument("--printer", default="generic")
    ap.add_argument("--nozzle", type=float, default=0.4)
    ap.add_argument("--layer-height", type=float, default=0.2)
    ap.add_argument("--profile", choices=["cosmetic", "structural"], default="structural")
    a = ap.parse_args()
    report = run(a.part, a.printer, a.nozzle, a.layer_height, a.profile)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["manufacturable"] else 1)
