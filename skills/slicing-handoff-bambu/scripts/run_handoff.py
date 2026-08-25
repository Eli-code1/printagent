"""Orchestrator: export 3MF + STEP, build the manifest, optionally slice."""
from __future__ import annotations

# Run under an interpreter that has the geometry packages. No-op when the current
# one already does; otherwise re-executes under the environment bootstrap_env.py
# set up, or exits with instructions instead of a ModuleNotFoundError traceback.
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while not _os.path.exists(_os.path.join(_d, "scripts", "printagent_env.py")):
    _p = _os.path.dirname(_d)
    if _p == _d:
        _d = None
        break
    _d = _p
if _d:
    _sys.path.insert(0, _os.path.join(_d, "scripts"))
    from printagent_env import ensure as _ensure
    _ensure()

import argparse
import contextlib
import json
import os
import sys

from export_3mf import export_3mf
from build_manifest import build_manifest
from slice_bambu import slice_bambu


@contextlib.contextmanager
def _stdout_to_stderr():
    """Point file descriptor 1 at stderr for the duration.

    Native libraries (OCCT, the Bambu CLI) write to the descriptor, not to
    sys.stdout, so a Python-level redirect misses them. Flush first, or buffered
    Python writes land in the wrong place on restore.
    """
    sys.stdout.flush()
    saved = os.dup(1)
    try:
        os.dup2(2, 1)
        yield
    finally:
        sys.stdout.flush()
        os.dup2(saved, 1)
        os.close(saved)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("part")
    ap.add_argument("--out", default="handoff")
    ap.add_argument("--printer", default="generic")
    ap.add_argument("--nozzle", type=float, default=0.4)
    ap.add_argument("--layer-height", type=float, default=0.2)
    ap.add_argument("--bed-type", default="textured_pei")
    ap.add_argument("--material", default="PLA")
    ap.add_argument("--supports", default="auto")
    ap.add_argument("--brim", default="on")
    ap.add_argument("--verification", default=None)
    ap.add_argument("--renders", default=None)
    ap.add_argument("--spec", default=None)
    ap.add_argument("--slice", action="store_true")
    ap.add_argument("--bambu-bin", default=None,
                    help="override; auto-detected from PATH and standard installs")
    a = ap.parse_args()

    # OCCT and the slicer both write to stdout, and OCCT is C++ writing straight
    # to file descriptor 1, so contextlib.redirect_stdout cannot catch it. Move
    # the descriptor itself to stderr for the duration, then restore it, so
    # stdout carries nothing but the JSON.
    with _stdout_to_stderr():
        geom = export_3mf(a.part, a.out)
        intent = {"printer_family": a.printer, "nozzle_mm": a.nozzle,
                  "layer_height_mm": a.layer_height, "bed_type": a.bed_type,
                  "supports": a.supports, "brim": a.brim,
                  "filament_slots_logical": [{"role": "primary", "material": a.material}]}
        manifest = build_manifest(a.out, geom, intent, a.verification, a.renders, a.spec)

        result = {"handoff_dir": a.out, "manifest": manifest}
        if a.slice:
            result["slice"] = slice_bambu(geom["model_3mf"], a.out, a.bambu_bin)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
