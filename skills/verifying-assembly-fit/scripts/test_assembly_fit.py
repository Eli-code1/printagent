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
from check_assembly_fit import (check_insertions, check_joints, measure_width,
                                place_parts)
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


def _frame(x_wall, y_wall, height):
    """Watertight rectangular tube from four butted wall boxes (no booleans),
    centered on the z axis with its bottom on z=0 (print pose)."""
    (ox, tx), (oy, ty) = x_wall, y_wall
    walls = []
    for sx in (-1, 1):
        b = trimesh.creation.box(extents=[tx, oy, height])
        b.apply_translation((sx * (ox - tx) / 2, 0, height / 2))
        walls.append(b)
    for sy in (-1, 1):
        b = trimesh.creation.box(extents=[ox - 2 * tx, ty, height])
        b.apply_translation((0, sy * (oy - ty) / 2, height / 2))
        walls.append(b)
    return trimesh.util.concatenate(walls)


def _tube_kit(tmp):
    # a hollow square collar (outer faces are the fit surface) dropping into a
    # deck throat: the parts/filament-trash-separator geometry in miniature
    collar = _frame((19.5, 2.0), (19.5, 2.0), 8)
    deck = _frame((30.0, 5.0), (30.0, 5.0), 6)
    collar.export(os.path.join(tmp, "collar.stl"))
    deck.export(os.path.join(tmp, "deck.stl"))
    man = {
        "name": "tube-in-slot", "printer": "bambu_x1c",
        "calibration": "calibrated",
        "parts": {
            "deck": {"mesh": "deck.stl", "print_rot_deg": [0, 0, 0],
                     "aabb_min": [0, 0, 0], "aabb_max": [30, 30, 6]},
            "collar": {"mesh": "collar.stl", "print_rot_deg": [0, 0, 0],
                       "aabb_min": [5.25, 5.25, 0],
                       "aabb_max": [24.75, 24.75, 8]},
        },
        "sequence": ["collar"],
        "insertions": {"collar": {"dir": [0, 0, -1], "travel": 12}},
        "joints": [{
            "name": "collar_in_throat", "type": "width", "intent": "slide",
            "inner": {"part": "deck", "kind": "slot", "nominal": 20.0,
                      "point": [15, 15, 3], "dir": [1, 0, 0], "span": [-2, 2],
                      "station_dir": [0, 0, 1]},
            "outer": {"part": "collar", "kind": "rail", "nominal": 19.5,
                      "point": [15, 15, 4], "dir": [1, 0, 0], "span": [-3, 3],
                      "station_dir": [0, 0, 1], "probe": "outer"},
        }],
    }
    path = os.path.join(tmp, "assembly.json")
    with open(path, "w") as f:
        json.dump(man, f)
    return path


def test_hollow_tube_in_slot():
    with tempfile.TemporaryDirectory() as tmp:
        path = _tube_kit(tmp)
        man = load_manifest(path)
        placed = place_parts(man, tmp)
        # the trap that motivates probe "outer": a centered origin sits in the
        # tube's void, so the default paired rays can only see the inner bore
        naive, _ = measure_width(placed["collar"]["mesh"], [15, 15, 4],
                                 [1, 0, 0], [-3, 3], 19.5, [0, 0, 1])
        assert naive is not None and abs(naive - 15.5) < 0.05, naive
        joints = check_joints(man, placed)
        j = joints[0]
        assert abs(j["inner"]["measured"] - 20.0) < 0.05, j["inner"]
        assert abs(j["outer"]["measured"] - 19.5) < 0.05, j["outer"]
        assert j["verdict"] == "PASS", j
        ins = check_insertions(man, placed)
        assert ins[0]["verdict"] == "PASS", ins


def test_probe_validation():
    # "probe" is only meaningful as "outer", on the rail of a width joint
    base = {
        "name": "v",
        "parts": {
            "a": {"mesh": "a.stl", "print_rot_deg": [0, 0, 0],
                  "aabb_min": [0, 0, 0], "aabb_max": [1, 1, 1]},
            "b": {"mesh": "b.stl", "print_rot_deg": [0, 0, 0],
                  "aabb_min": [0, 0, 0], "aabb_max": [1, 1, 1]},
        },
        "joints": [{
            "name": "j", "type": "width", "intent": "slide",
            "inner": {"part": "a", "kind": "slot", "nominal": 5.0,
                      "point": [0, 0, 0], "dir": [1, 0, 0], "span": [-1, 1]},
            "outer": {"part": "b", "kind": "rail", "nominal": 4.8,
                      "point": [0, 0, 0], "dir": [1, 0, 0], "span": [-1, 1]},
        }],
    }

    def rejects(mutate):
        man = json.loads(json.dumps(base))
        mutate(man)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "assembly.json")
            with open(path, "w") as f:
                json.dump(man, f)
            try:
                load_manifest(path)
            except SystemExit:
                return
        raise AssertionError(f"manifest should have been rejected: {man['joints']}")

    rejects(lambda m: m["joints"][0]["outer"].update(probe="sideways"))
    rejects(lambda m: m["joints"][0]["inner"].update(probe="outer"))
    rejects(lambda m: (m["joints"][0].update(type="cylinder"),
                       m["joints"][0]["outer"].update(probe="outer")))


if __name__ == "__main__":
    test_classify()
    test_measure_and_sweep()
    test_hollow_tube_in_slot()
    test_probe_validation()
    print("ok")
