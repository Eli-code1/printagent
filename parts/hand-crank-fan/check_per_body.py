"""Per-body min-wall verification for the print-in-place fan.

The combined-assembly min_wall gate reads the clearances *between* separate
bodies (meshing teeth, spin gaps) as if they were thin walls. To prove those are
intended clearances and not real thin walls, export each body alone and run the
authoritative ray-cast wall check on it. If every body passes on its own, the
only sub-threshold readings in the assembly are between-body gaps.
"""
from __future__ import annotations
import os
import sys

GEN = "/Users/eli/Downloads/bambuSlicerScripting/.claude/skills/generating-build123d/scripts"
GATE = "/Users/eli/Downloads/bambuSlicerScripting/.claude/skills/reviewing-manufacturability-fdm/scripts"
sys.path.insert(0, GATE)
sys.path.insert(0, GEN)

from export_part import export_part                       # noqa: E402
from geometry_io import load_mesh, sanitize, load_shape   # noqa: E402
from check_min_wall import check_min_wall                 # noqa: E402

import fan  # noqa: E402  (builds base, wheel, pinion at import)

T = 0.8  # cosmetic min wall for a 0.4 mm nozzle
print(f"per-body min-wall check, threshold = {T} mm\n")
all_pass = True
for name, body in [("base", fan.base), ("wheel", fan.wheel), ("pinion", fan.pinion),
                   ("pin", fan.pin_a)]:
    step = export_part(body, f"body_{name}")
    mesh, health = sanitize(load_mesh(step))
    shape = load_shape(step)
    r = check_min_wall(mesh, T, shape=shape)
    ray = r["methods"]["ray_thickness"]
    ok = r["passed"]
    all_pass = all_pass and bool(ok)
    print(f"{name:7s} watertight={health['watertight']!s:5s} "
          f"min_wall PASS={ok!s:5s} p1={ray['min_wall_mm']} raw_min={ray['raw_min_mm']} "
          f"thin_frac={ray['thin_area_fraction']} thin_n={ray['thin_sample_count']}/{ray['samples']}")
    for f in [f for f in os.listdir('.') if f.startswith(f"body_{name}.")]:
        os.remove(f)

print("\nALL BODIES PASS INDIVIDUALLY:", all_pass)
