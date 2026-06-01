"""Build every template and prove it passes the gate. Run this on any change to a
template. Each template's build() (and build_lid() where present) must produce a
part that the manufacturability gate calls manufacturable, and that matches the
invariants declared in its JSON sidecar.

Usage:
    python test_templates.py
"""
import glob
import importlib
import json
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))
sys.path.insert(0, os.path.join(_HERE, "..", "..", "reviewing-manufacturability-fdm", "scripts"))

from build123d import export_stl                     # noqa: E402
import trimesh                                        # noqa: E402
from run_checks import run                            # noqa: E402
from run_invariants import check_invariants           # noqa: E402


def main():
    tmp = tempfile.mkdtemp(prefix="templates_")
    metas = sorted(glob.glob(os.path.join(_HERE, "*.json")))
    fails = 0
    for mpath in metas:
        meta = json.load(open(mpath))
        name = meta["id"]
        mod = importlib.import_module(name)
        stl = os.path.join(tmp, name + ".stl")
        export_stl(mod.build(), stl)
        rep = run(stl, printer="bambu_x1c")
        mesh = trimesh.load(stl, force="mesh")
        inv = check_invariants(mesh, meta.get("invariants", {}))
        ok = rep["manufacturable"] and inv["passed"]
        fails += not ok
        print(f"{'ok ' if ok else 'XX '}{name:14} manufacturable={rep['manufacturable']} "
              f"hard_fails={rep['gates_failed']} warnings={rep['warnings']} "
              f"invariants={inv['passed']}")
        if not inv["passed"]:
            print("     invariant fixes:", inv["fixes"])
        if hasattr(mod, "build_lid"):
            lid_stl = os.path.join(tmp, name + "_lid.stl")
            export_stl(mod.build_lid(), lid_stl)
            rep2 = run(lid_stl, printer="bambu_x1c")
            lid_ok = rep2["manufacturable"]
            fails += not lid_ok
            print(f"     {'ok ' if lid_ok else 'XX '}{name}_lid manufacturable="
                  f"{rep2['manufacturable']} hard_fails={rep2['gates_failed']}")

    n = len(metas)
    print(f"\n{n - fails if fails <= n else 0} issues-free of {n} templates "
          f"({fails} failing checks)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
