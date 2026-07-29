"""Assembly manifest: the declared contract between a kit's parts and this
skill's checks. Loaded from a JSON file (conventionally assembly.json in the
kit's directory).

Shape:
{
  "name": "my-kit",
  "printer": "bambu_x1c", "material": "PLA",
  "nozzle_mm": 0.4, "layer_height_mm": 0.2,
  "calibration": "calibrated",              // or "generic"
  "parts": {
    "<instance>": {
      "mesh": "out/body.stl",               // print-pose mesh, bottom on z=0
      "print_rot_deg": [0, 0, 0],           // euler XYZ: print pose -> assembly
      "aabb_min": [x,y,z], "aabb_max": [x,y,z]   // assembly placement target
    }, ...
  },
  "sequence": ["axle_front", "wheel_fl", ...],   // arrival order of MOVING parts;
                                                  // parts not listed are static
  "insertions": {
    "<instance>": {"dir": [0,1,0], "travel": 38.0}   // seated <- start along -dir
  },
  "joints": [
    {
      "name": "wheel_fl_press", "type": "cylinder",   // or "width"
      "intent": "press",                              // press|snug|slide|running
      "inner": {"part": "wheel_fl", "kind": "bore", "nominal": 3.85,
                 "point": [x,y,z], "dir": [0,1,0], "span": [-3.5, 3.5]},
      "outer": {"part": "axle_front", "kind": "pin", "nominal": 4.0,
                 "point": [x,y,z], "dir": [0,1,0], "span": [-3.5, 3.5]}
    }, ...
  ]
}

For "cylinder" joints, point+dir is the shared axis in ASSEMBLY coordinates and
span brackets the engagement zone along it (offsets from point). For "width"
joints (tongue/dovetail), dir is the width direction; span offsets run along
the optional "station_dir" (defaults to the axis orthogonal to dir and Z).

Width features are measured by paired rays cast from point outward along
+-dir, so point must sit in the slot's void or the rail's solid. A HOLLOW rail
(a tube whose OUTER faces are the fit surface) has no such interior point: any
centered origin sits in the internal void and the rays report the bore, not
the outer width. Declare "probe": "outer" on that rail and the checker instead
casts each ray pair inward from outside the part's bounds, measuring the outer
envelope along the station line. "probe" is only valid as "outer", on the rail
of a width joint.
"""
from __future__ import annotations
import json
import math

import numpy as np


REQUIRED_PART_KEYS = {"mesh", "print_rot_deg", "aabb_min", "aabb_max"}
REQUIRED_FEATURE_KEYS = {"part", "kind", "nominal", "point", "dir", "span"}
FEATURE_KINDS = {"bore", "pin", "slot", "rail"}
JOINT_TYPES = {"cylinder", "width"}


def euler_matrix(rx, ry, rz):
    m = np.eye(3)
    for axis, deg in (((1, 0, 0), rx), ((0, 1, 0), ry), ((0, 0, 1), rz)):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        x, y, z = axis
        if deg:
            k = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]], dtype=float)
            m = (np.eye(3) + math.sin(a) * k + (1 - math.cos(a)) * k @ k) @ m
    return m


def load_manifest(path: str) -> dict:
    with open(path) as f:
        man = json.load(f)
    problems = []
    for key in ("name", "parts", "joints"):
        if key not in man:
            problems.append(f"manifest missing '{key}'")
    for name, p in man.get("parts", {}).items():
        missing = REQUIRED_PART_KEYS - set(p)
        if missing:
            problems.append(f"part '{name}' missing {sorted(missing)}")
    for j in man.get("joints", []):
        if j.get("type") not in JOINT_TYPES:
            problems.append(f"joint '{j.get('name')}' bad type {j.get('type')}")
        for side in ("inner", "outer"):
            feat = j.get(side, {})
            missing = REQUIRED_FEATURE_KEYS - set(feat)
            if missing:
                problems.append(f"joint '{j.get('name')}' {side} missing "
                                f"{sorted(missing)}")
            elif feat["kind"] not in FEATURE_KINDS:
                problems.append(f"joint '{j.get('name')}' {side} bad kind")
            elif feat["part"] not in man.get("parts", {}):
                problems.append(f"joint '{j.get('name')}' references unknown "
                                f"part '{feat['part']}'")
            probe = feat.get("probe")
            if probe is not None and (probe != "outer"
                                      or j.get("type") != "width"
                                      or feat.get("kind") != "rail"):
                problems.append(f"joint '{j.get('name')}' {side}: probe must "
                                f"be \"outer\", and only on a width-joint rail")
    for name in man.get("sequence", []):
        if name not in man.get("parts", {}):
            problems.append(f"sequence references unknown part '{name}'")
        elif name not in man.get("insertions", {}):
            problems.append(f"moving part '{name}' has no insertion entry")
    if problems:
        raise SystemExit("invalid manifest:\n  " + "\n  ".join(problems))
    man.setdefault("calibration", "calibrated")
    man.setdefault("nozzle_mm", 0.4)
    man.setdefault("layer_height_mm", 0.2)
    man.setdefault("sequence", [])
    man.setdefault("insertions", {})
    return man
