"""Quick matplotlib previews of the fit-check coupon (no GL/pyglet needed)."""
from __future__ import annotations
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

os.makedirs("renders", exist_ok=True)
m = trimesh.load("coupon.stl", force="mesh")
ctr = m.vertices.mean(axis=0)
rng = (m.vertices.max(axis=0) - m.vertices.min(axis=0)).max() / 2.0


def draw(ax, elev, azim, zscale=1.0):
    tris = m.vertices[m.faces]
    pc = Poly3DCollection(tris, facecolor="#7f929e", edgecolor="#3d4a52",
                          linewidths=0.05, alpha=1.0)
    ax.add_collection3d(pc)
    ax.set_xlim(ctr[0] - rng, ctr[0] + rng)
    ax.set_ylim(ctr[1] - rng, ctr[1] + rng)
    ax.set_zlim(ctr[2] - rng * zscale, ctr[2] + rng * zscale)
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


views = {"iso": (28, -55), "top": (88, -90), "front": (8, -90), "low": (12, -35)}
for name, (elev, azim) in views.items():
    fig = plt.figure(figsize=(7, 5.4), dpi=150)
    ax = fig.add_subplot(111, projection="3d")
    draw(ax, elev, azim)
    fig.tight_layout(pad=0)
    fig.savefig(f"renders/{name}.png", bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print("wrote renders/" + name + ".png")
