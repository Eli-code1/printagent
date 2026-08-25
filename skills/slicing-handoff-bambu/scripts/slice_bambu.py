"""Optional: slice model.3mf with the Bambu Studio CLI. Slicing only; printing is downstream.
Always uses a per-plate timeout and a sandboxed temp dir."""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import tempfile

# Used when the caller passes no profiles; the CLI segfaults with none loaded.
DEFAULT_PROFILES = {"machine": "Bambu Lab X1 Carbon 0.4 nozzle",
                    "process": "0.20mm Standard @BBL X1C",
                    "filament": "Bambu PLA Basic @BBL X1C"}

# Standard install locations, tried in order when the caller passes no explicit
# path. Most users never have to name the binary; --bambu-bin stays the override
# for a non-standard install.
STANDARD_BINS = [
    "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
    "~/Applications/BambuStudio.app/Contents/MacOS/BambuStudio",
    "/usr/bin/bambu-studio",
    "/usr/local/bin/bambu-studio",
    "/opt/bambu-studio/bambu-studio",
    "~/.local/bin/bambu-studio",
]


def find_bambu_bin(bambu_bin=None):
    """Resolve the Bambu Studio CLI. An explicit path or command name wins; then
    PATH; then the standard install locations. Returns None when nothing exists."""
    if bambu_bin:
        found = shutil.which(bambu_bin)
        if found:
            return found
        expanded = os.path.expanduser(bambu_bin)
        return expanded if os.path.exists(expanded) else None
    found = shutil.which("bambu-studio")
    if found:
        return found
    for cand in STANDARD_BINS:
        expanded = os.path.expanduser(cand)
        if os.path.exists(expanded):
            return expanded
    return None


def _flatten_profile(bbl_dir, folder, name, out_dir):
    """The CLI does not resolve `inherits` chains in bundled profiles; merge them."""
    def merge(n):
        with open(os.path.join(bbl_dir, folder, n + ".json")) as f:
            data = json.load(f)
        parent = data.pop("inherits", None)
        if parent:
            base = merge(parent)
            base.update(data)
            return base
        return data
    out = os.path.join(out_dir, f"{folder}_{name}.json".replace(" ", "_"))
    with open(out, "w") as f:
        json.dump(merge(name), f)
    return out


def slice_bambu(model_3mf, out_dir, bambu_bin=None,
                settings=None, filaments=None, mstpp=300, timeout=900):
    binp = find_bambu_bin(bambu_bin)
    if binp is None:
        where = bambu_bin if bambu_bin else "PATH or a standard install location"
        return {"sliced": False, "note": f"Bambu Studio CLI not found ({where}); "
                                         f"install it, pass --bambu-bin, or skip --slice"}
    # The CLI chdirs mid-run, so relative paths break; --export-3mf must be absolute.
    out_gcode = os.path.abspath(os.path.join(out_dir, "model.gcode.3mf"))

    with tempfile.TemporaryDirectory() as tmp:
        if not settings or not filaments:
            bbl = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(binp)),
                                                "..", "Resources", "profiles", "BBL"))
            if not os.path.isdir(bbl):
                return {"sliced": False,
                        "note": f"no profiles passed and none found at {bbl}; slicing "
                                f"without machine/process/filament settings crashes the CLI"}
            if not settings:
                settings = [_flatten_profile(bbl, "machine", DEFAULT_PROFILES["machine"], tmp),
                            _flatten_profile(bbl, "process", DEFAULT_PROFILES["process"], tmp)]
            if not filaments:
                filaments = [_flatten_profile(bbl, "filament", DEFAULT_PROFILES["filament"], tmp)]

        # --orient/--arrange take explicit values in Studio >= 02.07 (0-disable, 1-enable)
        cmd = [binp, "--slice", "0", "--orient", "1", "--arrange", "1",
               "--mstpp", str(mstpp),
               "--load-settings", ";".join(settings),
               "--load-filaments", ";".join(filaments),
               "--export-3mf", out_gcode, os.path.abspath(model_3mf)]
        env = {**os.environ, "TMPDIR": tmp}
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return {"sliced": False, "note": "slice timed out (pathological mesh?)"}

    ok = r.returncode == 0 and os.path.exists(out_gcode)
    if ok:
        note = "ok"
    else:
        text = (r.stderr or "") + (r.stdout or "")
        errs = [ln for ln in text.splitlines() if "error" in ln.lower()]
        note = ("\n".join(errs) or text.strip())[-400:] or f"exit code {r.returncode}"
    return {"sliced": ok, "gcode_3mf": out_gcode if ok else None, "note": note}
