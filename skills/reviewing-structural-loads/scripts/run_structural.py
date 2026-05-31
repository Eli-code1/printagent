"""Orchestrator -> structural_review.json (advisory reviewer, not a hard gate)."""
from __future__ import annotations
import argparse
import json

from geometry_io import load_mesh, sanitize
from mass_properties import mass_properties
from check_layer_anisotropy import check_layer_anisotropy
from check_stress_risers import check_stress_risers

DENSITY = {"PLA": 1.24, "PETG": 1.27, "ABS": 1.04, "ASA": 1.07, "PC": 1.20,
           "NYLON": 1.14, "TPU": 1.21, "PLA-CF": 1.30, "PETG-CF": 1.30}


def run(path, load_dir=(0, 0, 1), material="PLA", infill=0.25):
    mesh = sanitize(load_mesh(path))
    dens = DENSITY.get(material.upper(), 1.24)
    checks = [
        mass_properties(mesh, dens, infill),
        check_layer_anisotropy(mesh, load_dir),
        check_stress_risers(mesh),
    ]
    warns = [c["name"] for c in checks if c.get("passed") is False]
    verdict = "review concerns: " + ", ".join(warns) if warns else "no structural concerns flagged"
    return {"part": path, "material": material, "infill": infill,
            "load_dir": list(load_dir), "verdict": verdict,
            "checks": checks, "warnings": warns}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("part")
    ap.add_argument("--load-dir", type=float, nargs=3, default=[0, 0, 1])
    ap.add_argument("--material", default="PLA")
    ap.add_argument("--infill", type=float, default=0.25)
    a = ap.parse_args()
    print(json.dumps(run(a.part, tuple(a.load_dir), a.material, a.infill), indent=2))
