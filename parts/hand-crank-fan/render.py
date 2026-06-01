"""Quick matplotlib previews of the fan (no GL/pyglet needed). Colors the three
bodies so the wheel, the impeller-pinion, and the reclining base read clearly."""
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
from build123d import Compound  # noqa: E402
bodies = {"base": (fan.base, "#b9c0c9"), "wheel": (fan.wheel, "#4c78c8"),
          "pinion": (fan.pinion, "#f58518"),
          "pins": (Compound(children=[fan.pin_a, fan.pin_b]), "#444444")}
ALPHA = {"base": 0.16, "wheel": 1.0, "pinion": 1.0, "pins": 1.0}
meshes = {}
for name, (body, _c) in bodies.items():
    export_part(body, f"_r_{name}", also_stl=True)
    meshes[name] = trimesh.load(f"_r_{name}.stl", force="mesh")

allv = np.vstack([m.vertices for m in meshes.values()])
ctr = allv.mean(axis=0)
rng = (allv.max(axis=0) - allv.min(axis=0)).max() / 2.0


def draw(ax, elev, azim, names=None):
    for name, (_b, color) in bodies.items():
        if names is not None and name not in names:
            continue
        m = meshes[name]
        tris = m.vertices[m.faces]
        a = ALPHA[name]
        pc = Poly3DCollection(tris, alpha=a, facecolor=color,
                              edgecolor=(0, 0, 0, 0.06 if a > 0.5 else 0.0),
                              linewidths=0.1)
        # cheap shading by face-normal Z
        nz = m.face_normals[:, 2]
        shade = 0.55 + 0.45 * (nz - nz.min()) / (np.ptp(nz) + 1e-9)
        base = np.array(matplotlib.colors.to_rgb(color))
        pc.set_facecolor(np.column_stack([(base[None, :] * shade[:, None]).clip(0, 1),
                                          np.full(len(shade), a)]))
        ax.add_collection3d(pc)
    ax.set_xlim(ctr[0] - rng, ctr[0] + rng)
    ax.set_ylim(ctr[1] - rng, ctr[1] + rng)
    ax.set_zlim(ctr[2] - rng, ctr[2] + rng)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


views = {"iso": (22, -60, None), "front": (10, -90, None), "side": (6, 0, None),
         "mechanism": (35, -65, {"wheel", "pinion"})}
for vname, (elev, azim, names) in views.items():
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection="3d")
    draw(ax, elev, azim, names)
    fig.tight_layout()
    fig.savefig(f"renders/{vname}.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    print("wrote", f"renders/{vname}.png")

for name in bodies:
    for ext in ("step", "stl"):
        f = f"_r_{name}.{ext}"
        if os.path.exists(f):
            os.remove(f)
