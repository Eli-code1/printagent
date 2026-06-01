"""Top-down render of the print plate (the 5 parts laid out on the bed)."""
from __future__ import annotations
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

GEN = "/Users/eli/Downloads/bambuSlicerScripting/.claude/skills/generating-build123d/scripts"
sys.path.insert(0, GEN)
from export_part import export_part  # noqa: E402
import trimesh  # noqa: E402
import fan  # noqa: E402

os.makedirs("renders", exist_ok=True)
export_part(fan.print_plate, "_plate", also_stl=True)
m = trimesh.load("_plate.stl", force="mesh")
fig = plt.figure(figsize=(7, 7))
ax = fig.add_subplot(111, projection="3d")
tris = m.vertices[m.faces]
nz = m.face_normals[:, 2]
shade = 0.55 + 0.45 * (nz - nz.min()) / (np.ptp(nz) + 1e-9)
pc = Poly3DCollection(tris, edgecolor=(0, 0, 0, 0.05), linewidths=0.1)
base = np.array(matplotlib.colors.to_rgb("#6699cc"))
pc.set_facecolor((base[None, :] * shade[:, None]).clip(0, 1))
ax.add_collection3d(pc)
c = m.vertices.mean(0)
r = (m.vertices.max(0) - m.vertices.min(0)).max() / 2
ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=70, azim=-90); ax.set_axis_off()
fig.savefig("renders/plate.png", dpi=130, bbox_inches="tight")
print("wrote renders/plate.png")
for e in (".stl", ".step"):
    if os.path.exists("_plate" + e):
        os.remove("_plate" + e)
