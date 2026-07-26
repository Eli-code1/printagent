"""Smoke tests: fit classification windows, and ray measurement + insertion
sweep on a tiny synthetic two-part kit (a pin-in-bore block), no build123d
needed. Run: python test_assembly_fit.py"""
from __future__ import annotations
import json
import os
import sys
import tempfile

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_rules
from check_assembly_fit import (check_insertions, check_joints, place_parts)
from assembly_schema import load_manifest


def test_classify():
    assert fit_rules.classify(-0.20, -0.15, -0.10, "press")[0] == "PASS"
    assert fit_rules.classify(0.25, 0.35, 0.45, "running")[0] == "PASS"
    assert fit_rules.classify(-0.5, -0.45, -0.40, "press")[0] == "FAIL"
    v, advice = fit_rules.classify(0.9, 1.0, 1.1, "running")
    assert v == "FAIL" and "shrink" in advice
    # in-window mid with a big tail spill -> WARN, not PASS
    assert fit_rules.classify(-0.44, -0.20, 0.04, "press")[0] == "WARN"
    # just outside the window -> WARN with no dimensional edit demanded
    assert fit_rules.classify(-0.10, 0.04, 0.18, "press")[0] == "WARN"


def _kit(tmp):
    # a bored block (watertight annulus, no boolean backend needed) and a pin
    # that inserts from above
    block = trimesh.creation.annulus(r_min=2.0, r_max=6.0, height=10,
                                     sections=64)
    pin = trimesh.creation.cylinder(radius=1.9, height=14, sections=64)
    pin.apply_translation((0, 0, 7))
    block.export(os.path.join(tmp, "block.stl"))
    pin.export(os.path.join(tmp, "pin.stl"))
    man = {
        "name": "smoke", "printer": "bambu_x1c",
        "calibration": "calibrated",
        "parts": {
            "block": {"mesh": "block.stl", "print_rot_deg": [0, 0, 0],
                      "aabb_min": [4, 4, 0], "aabb_max": [16, 16, 10]},
            "pin": {"mesh": "pin.stl", "print_rot_deg": [0, 0, 0],
                    "aabb_min": [8.1, 8.1, 2], "aabb_max": [11.9, 11.9, 16]},
        },
        "sequence": ["pin"],
        "insertions": {"pin": {"dir": [0, 0, -1], "travel": 15}},
        "joints": [{
            "name": "pin_in_block", "type": "cylinder", "intent": "snug",
            "inner": {"part": "block", "kind": "bore", "nominal": 4.0,
                      "point": [10, 10, 5], "dir": [0, 0, 1], "span": [-4, 4]},
            "outer": {"part": "pin", "kind": "pin", "nominal": 3.8,
                      "point": [10, 10, 9], "dir": [0, 0, 1], "span": [-5, 5]},
        }],
    }
    path = os.path.join(tmp, "assembly.json")
    with open(path, "w") as f:
        json.dump(man, f)
    return path


def test_measure_and_sweep():
    with tempfile.TemporaryDirectory() as tmp:
        path = _kit(tmp)
        man = load_manifest(path)
        placed = place_parts(man, tmp)
        joints = check_joints(man, placed)
        j = joints[0]
        assert abs(j["inner"]["measured"] - 4.0) < 0.05, j["inner"]
        assert abs(j["outer"]["measured"] - 3.8) < 0.05, j["outer"]
        assert j["verdict"] in ("PASS", "WARN"), j
        ins = check_insertions(man, placed)
        assert ins[0]["verdict"] == "PASS", ins


if __name__ == "__main__":
    test_classify()
    test_measure_and_sweep()
    print("ok")
