"""Given a failure-mode key, return its classification, causes, remedy, and route."""
from __future__ import annotations
import argparse
import json
import sys

from failure_db import FAILURES


def route(mode: str) -> dict:
    key = mode.strip().lower().replace(" ", "_").replace("-", "_")
    if key not in FAILURES:
        return {"error": f"unknown failure mode '{mode}'",
                "known": sorted(FAILURES.keys())}
    f = FAILURES[key]
    action = ("hand a geometry edit back to generating-build123d, then re-run the gate"
              if f["route"] == "generating-build123d" else
              "emit a setting recommendation for the slicing/printer agent (advisory only)"
              if f["route"] == "slicer_printer" else
              "apply the geometry edit AND emit a process hint")
    return {"failure": key, "classification": f["class"], "route": f["route"],
            "visual_signs": f["signs"], "design_fix": f["design_fix"],
            "process_fix": f["process_fix"], "recommended_action": action}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", help="failure mode, e.g. warping, layer_shift, delamination")
    a = ap.parse_args()
    out = route(a.mode)
    print(json.dumps(out, indent=2))
    sys.exit(1 if "error" in out else 0)
