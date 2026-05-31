"""Orchestrator: export 3MF + STEP, build the manifest, optionally slice."""
from __future__ import annotations
import argparse
import json

from export_3mf import export_3mf
from build_manifest import build_manifest
from slice_bambu import slice_bambu


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
    ap.add_argument("--bambu-bin", default="bambu-studio")
    a = ap.parse_args()

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
