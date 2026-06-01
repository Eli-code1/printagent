"""Snap-together spin/fit/mesh check (flat bodies).

Confirms, geometrically:
  - fits: gear bore vs pin shaft (spin), base hole vs shaft (press), head vs bore (retention)
  - each gear sits on its pin with clearance (free to spin) and is held captive by the head
  - the two gears still mesh and drive with backlash, no jam over a tooth cycle
  - the fan blades clear the wheel as they sweep over it
"""
from __future__ import annotations
import sys
import numpy as np
import trimesh

GEN = "/Users/eli/Downloads/bambuSlicerScripting/.claude/skills/generating-build123d/scripts"
sys.path.insert(0, GEN)
from export_part import export_part  # noqa: E402
import fan  # noqa: E402

for nm, body in [("base", fan.build_base()), ("wheel", fan.build_wheel()),
                 ("pinion", fan.build_pinion_rotor()),
                 ("pinA", fan.seat_pin(0.0)), ("pinB", fan.seat_pin(fan.CD))]:
    export_part(body, "_s_" + nm, also_stl=True)
M = {nm: trimesh.load(f"_s_{nm}.stl", force="mesh")
     for nm in ("base", "wheel", "pinion", "pinA", "pinB")}
RATIO = fan.Z_WHEEL / fan.Z_PINION


def zrot(mesh, deg, cx, cy):
    m = mesh.copy()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(deg), [0, 0, 1], [cx, cy, 0]))
    return m


def clr(A, B):
    return float(-max(A.nearest.signed_distance(B.vertices).max(),
                      B.nearest.signed_distance(A.vertices).max()))


print("=== fits (mm) ===")
print(f"  gear bore D{2*fan.GEAR_BORE_R:.1f} on shaft D{2*fan.PIN_SHAFT_R:.1f} "
      f"-> spin clearance {2*(fan.GEAR_BORE_R-fan.PIN_SHAFT_R):.2f} dia")
print(f"  base hole D{2*fan.BASE_HOLE_R:.1f} vs shaft D{2*fan.PIN_SHAFT_R:.1f} "
      f"-> press interference {2*(fan.PIN_SHAFT_R-fan.BASE_HOLE_R):.2f} dia")
print(f"  head D{2*fan.PIN_HEAD_R:.1f} vs bore D{2*fan.GEAR_BORE_R:.1f} "
      f"-> retention ledge {(fan.PIN_HEAD_R-fan.GEAR_BORE_R):.2f} radial")

print("\n=== assembled clearances (angle 0) ===")
c_wp = clr(M["wheel"], M["pinion"])
c_wpa = clr(M["wheel"], M["pinA"])
c_ppb = clr(M["pinion"], M["pinB"])
c_wb = clr(M["wheel"], M["base"])
c_pb = clr(M["pinion"], M["base"])
print(f"  wheel <-> pinion (mesh+blades): {c_wp:+.3f}")
print(f"  wheel <-> its pin (spins on shaft): {c_wpa:+.3f}")
print(f"  pinion <-> its pin (spins on shaft): {c_ppb:+.3f}")
print(f"  wheel <-> base (rests on deck): {c_wb:+.3f}")
print(f"  pinion <-> base (rests on deck): {c_pb:+.3f}")

print("\n=== spin one tooth cycle (synced) ===")
worst_wp = 9e9
for a in np.linspace(0, 360.0 / fan.Z_WHEEL, 13):
    w = zrot(M["wheel"], a, 0, 0)
    p = zrot(M["pinion"], -a * RATIO, fan.CD, 0)
    worst_wp = min(worst_wp, clr(w, p))
print(f"  worst wheel<->pinion (mesh + blade-over-wheel) over cycle: {worst_wp:+.3f}")

spins = (worst_wp > -0.10 and c_wpa > 0.0 and c_ppb > 0.0
         and fan.PIN_HEAD_R > fan.GEAR_BORE_R and fan.PIN_SHAFT_R > fan.BASE_HOLE_R)
print(f"\nVERDICT: assembles, retained, and spins free? {spins}")

import os
for nm in ("base", "wheel", "pinion", "pinA", "pinB"):
    for e in (".stl", ".step"):
        if os.path.exists(f"_s_{nm}{e}"):
            os.remove(f"_s_{nm}{e}")
