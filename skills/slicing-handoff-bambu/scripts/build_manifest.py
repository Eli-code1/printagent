"""Assemble the handoff directory and write manifest.json + provenance.json."""
from __future__ import annotations
import datetime
import hashlib
import json
import os
import shutil


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def build_manifest(out_dir, geom, intent, verification_path=None,
                   renders_dir=None, spec_path=None):
    os.makedirs(out_dir, exist_ok=True)

    verification = {"manufacturable": None, "gates_passed": [], "gates_failed": [], "warnings": []}
    if verification_path and os.path.exists(verification_path):
        shutil.copyfile(verification_path, os.path.join(out_dir, "verification.json"))
        rep = json.load(open(verification_path))
        verification = {k: rep.get(k) for k in
                        ("manufacturable", "gates_passed", "gates_failed", "warnings")}

    if renders_dir and os.path.isdir(renders_dir):
        dst = os.path.join(out_dir, "renders")
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(renders_dir, dst)

    if spec_path and os.path.exists(spec_path):
        shutil.copyfile(spec_path, os.path.join(out_dir, "spec.json"))

    files = {}
    for name in ("model.3mf", "model.step"):
        p = os.path.join(out_dir, name)
        if os.path.exists(p):
            files[name] = _sha256(p)

    provenance = {"created_utc": datetime.datetime.utcnow().isoformat() + "Z",
                  "spec_ref": "spec.json" if spec_path else None, "files": files}
    json.dump(provenance, open(os.path.join(out_dir, "provenance.json"), "w"), indent=2)

    manifest = {
        "geometry": {"units": "mm", "bbox_mm": geom.get("bbox_mm"),
                     "watertight": geom.get("watertight"), "n_faces": geom.get("n_faces")},
        "print_intent": {"_note": "hints, overridable; embedded 3MF presets win if present",
                         **intent},
        "verification": verification,
        "provenance": provenance,
    }
    json.dump(manifest, open(os.path.join(out_dir, "manifest.json"), "w"), indent=2)
    return manifest
