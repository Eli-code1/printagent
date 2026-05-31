"""Optional: slice model.3mf with the Bambu Studio CLI. Slicing only; printing is downstream.
Always uses a per-plate timeout and a sandboxed temp dir."""
from __future__ import annotations
import os
import shutil
import subprocess
import tempfile


def slice_bambu(model_3mf, out_dir, bambu_bin="bambu-studio",
                settings=None, filaments=None, mstpp=300, timeout=900):
    binp = shutil.which(bambu_bin) or (bambu_bin if os.path.exists(bambu_bin) else None)
    if binp is None:
        return {"sliced": False, "note": f"Bambu Studio CLI not found ({bambu_bin}); "
                                         f"install it or skip --slice"}
    out_gcode = os.path.join(out_dir, "model.gcode.3mf")
    cmd = [binp, "--slice", "0", "--orient", "--arrange", "1",
           "--mstpp", str(mstpp), "--export-3mf", out_gcode]
    if settings:
        cmd += ["--load-settings", ";".join(settings)]
    if filaments:
        cmd += ["--load-filaments", ";".join(filaments)]
    cmd += [model_3mf]

    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "TMPDIR": tmp}
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return {"sliced": False, "note": "slice timed out (pathological mesh?)"}
    ok = r.returncode == 0 and os.path.exists(out_gcode)
    return {"sliced": ok, "gcode_3mf": out_gcode if ok else None,
            "note": (r.stderr or r.stdout).strip()[-400:] if not ok else "ok"}
