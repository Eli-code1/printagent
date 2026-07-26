"""Verify that a multi-part FDM kit will assemble in real life.

Reads an assembly manifest (see assembly_schema.py), places every part's
print-pose mesh into the assembly frame, then:

1. MEASURES each declared joint feature from the built mesh by ray probing
   (robust to sparse STL tessellation, unlike vertex sampling): bores/pins by
   radial rays from the shared axis, slots/rails by paired rays along the
   width direction.
2. MODELS the as-printed dimension: each feature is classified axial/lateral
   against its own part's build axis and given the (mu, sigma) error from
   fit_rules, plus seam bulge on vertical pins and an elephant-foot note for
   features that touch their part's bed plane.
3. CLASSIFIES the effective clearance band against the joint's declared
   intent (press / snug / slide / running): PASS, WARN, or FAIL with a
   concrete dimensional edit.
4. SWEEPS each moving part along its declared insertion path, in sequence
   order, against everything already assembled: collisions during travel fail
   the assembly even when the seated fit is fine.

Usage:
    python check_assembly_fit.py ASSEMBLY.json [--out assembly_fit.json]

Exit 0 when nothing FAILs (warnings allowed), 1 otherwise.
"""
from __future__ import annotations
import argparse
import json
import os
import sys

import numpy as np
import trimesh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_rules
from assembly_schema import euler_matrix, load_manifest


def _unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def _basis(axis):
    axis = _unit(axis)
    helper = np.array([0.0, 0.0, 1.0])
    if abs(axis @ helper) > 0.9:
        helper = np.array([1.0, 0.0, 0.0])
    u = _unit(np.cross(axis, helper))
    return u, np.cross(axis, u)


def place_parts(man, base_dir):
    placed = {}
    for name, spec in man["parts"].items():
        mesh = trimesh.load(os.path.join(base_dir, spec["mesh"]))
        R = euler_matrix(*spec["print_rot_deg"])
        m4 = np.eye(4)
        m4[:3, :3] = R
        mesh.apply_transform(m4)
        t = np.array(spec["aabb_min"]) - mesh.bounds[0]
        mesh.apply_translation(t)
        err = float(np.abs(mesh.bounds[1] - np.array(spec["aabb_max"])).max())
        placed[name] = {"mesh": mesh, "R": R, "t": t, "placement_err": err}
    return placed


def ray_hits(mesh, origins, dirs):
    loc, idx, _ = mesh.ray.intersects_location(origins, dirs,
                                               multiple_hits=False)
    d = np.full(len(origins), np.nan)
    for l, i in zip(loc, idx):
        dist = float(np.linalg.norm(l - origins[i]))
        if not np.isfinite(d[i]) or dist < d[i]:
            d[i] = dist
    return d


def measure_cylinder(mesh, point, axis, span, nominal, n_ang=16, n_st=5):
    """Diameter of a bore (rays cast from inside the void) or a pin (rays cast
    from inside the solid) around the declared axis. Returns (median, spread)."""
    axis = _unit(axis)
    u, v = _basis(axis)
    point = np.asarray(point, dtype=float)
    origins, dirs = [], []
    for s in np.linspace(span[0], span[1], n_st):
        o = point + axis * s
        for a in np.linspace(0, 2 * np.pi, n_ang, endpoint=False):
            origins.append(o)
            dirs.append(np.cos(a) * u + np.sin(a) * v)
    d = ray_hits(mesh, np.array(origins), np.array(dirs))
    r = d[np.isfinite(d) & (d < nominal * 0.5 * 1.6)]
    if len(r) < n_ang:
        return None, None
    return 2 * float(np.median(r)), 2 * float(np.percentile(r, 95)
                                              - np.percentile(r, 5))


def measure_width(mesh, point, wdir, span, nominal, station_dir, n_st=5):
    """Width across a slot (origin in the void) or a rail (origin in the
    solid): paired rays along +-wdir from stations along station_dir."""
    wdir = _unit(wdir)
    station_dir = _unit(station_dir)
    point = np.asarray(point, dtype=float)
    origins, dirs = [], []
    for s in np.linspace(span[0], span[1], n_st):
        o = point + station_dir * s
        origins += [o, o]
        dirs += [wdir, -wdir]
    d = ray_hits(mesh, np.array(origins), np.array(dirs))
    widths = []
    for i in range(0, len(d), 2):
        if np.isfinite(d[i]) and np.isfinite(d[i + 1]):
            w = d[i] + d[i + 1]
            if w < nominal * 1.6:
                widths.append(w)
    if len(widths) < 2:
        return None, None
    return float(np.median(widths)), float(np.ptp(widths))


def feature_orientation(feat, joint_type, R):
    """axial/lateral of the controlling dimension vs the part's build axis."""
    d_print = R.T @ _unit(feat["dir"])
    along_z = abs(float(d_print[2]))
    if joint_type == "cylinder":
        return "axial" if along_z > 0.7 else "lateral"
    return "lateral" if along_z > 0.7 else "axial"


def feature_bed_z(feat, joint_type, R, t, nominal):
    """Lowest print-frame z the feature reaches (elephant-foot exposure)."""
    point = np.asarray(feat["point"], dtype=float)
    axis = _unit(feat["dir"])
    zs = []
    for s in feat["span"]:
        p_print = R.T @ (point + axis * s - t)
        drop = nominal / 2 if joint_type == "cylinder" else 0.0
        zs.append(float(p_print[2]) - drop)
    return min(zs)


def check_joints(man, placed):
    results = []
    lh, cal = man["layer_height_mm"], man["calibration"]
    for j in man["joints"]:
        row = {"name": j["name"], "intent": j["intent"], "type": j["type"]}
        sides = {}
        for side in ("inner", "outer"):
            feat = j[side]
            part = placed[feat["part"]]
            if j["type"] == "cylinder":
                meas, spread = measure_cylinder(
                    part["mesh"], feat["point"], feat["dir"], feat["span"],
                    feat["nominal"])
            else:
                station_dir = feat.get("station_dir")
                if station_dir is None:
                    station_dir = np.cross(_unit(feat["dir"]), [0, 0, 1.0])
                meas, spread = measure_width(
                    part["mesh"], feat["point"], feat["dir"], feat["span"],
                    feat["nominal"], station_dir)
            if meas is None:
                row["verdict"] = "FAIL"
                row["advice"] = (f"{side} feature on '{feat['part']}' not found "
                                 f"where declared; manifest and geometry disagree.")
                break
            orient = feature_orientation(feat, j["type"], part["R"])
            mu, sigma = fit_rules.dimension_error(feat["kind"], orient, lh, cal)
            notes = []
            if feat["kind"] == "pin" and orient == "axial":
                mu += fit_rules.SEAM_BULGE / 2      # seam ridge runs the pin
                notes.append("vertical pin: perimeter seam adds a local ridge")
            if feat["kind"] == "bore" and orient == "lateral":
                notes.append("horizontal bore: expect vertical sag; ream if tight")
            zmin = feature_bed_z(feat, j["type"], part["R"], part["t"],
                                 feat["nominal"])
            if zmin < fit_rules.ELEPHANT_BAND_MM:
                notes.append("touches its bed plane: elephant-foot flare "
                             f"(+{fit_rules.ELEPHANT_FOOT} worst) unless the "
                             "first edge is chamfered or de-flared in the slicer")
            sides[side] = {"part": feat["part"], "kind": feat["kind"],
                           "nominal": feat["nominal"],
                           "measured": round(meas, 3),
                           "measure_spread": round(spread, 3),
                           "orientation": orient,
                           "model_mu": round(mu, 3), "model_sigma": round(sigma, 3),
                           "print_notes": notes}
        else:
            inner, outer = sides["inner"], sides["outer"]
            if (j["type"] == "cylinder"
                    and inner["orientation"] == "lateral"
                    and outer["orientation"] == "lateral"):
                # anisotropic pair (e.g. lying rod in a horizontal sleeve):
                # evaluate the vertical and horizontal gaps separately and
                # take the controlling (smaller) one
                per_axis = {}
                for ax in ("v", "h"):
                    mu_i = fit_rules.LATERAL_CYL_AXES["bore"][ax]
                    mu_o = fit_rules.LATERAL_CYL_AXES["pin"][ax]
                    per_axis[ax] = fit_rules.effective_clearance(
                        inner["measured"], (mu_i, inner["model_sigma"]),
                        outer["measured"], (mu_o, outer["model_sigma"]))
                ax = min(per_axis, key=lambda k: per_axis[k][1])
                lo, mid, hi = per_axis[ax]
                inner["print_notes"].append(
                    f"lateral/lateral pair: controlling axis is "
                    f"{'vertical (bore sag)' if ax == 'v' else 'horizontal (pin squish)'}")
            else:
                lo, mid, hi = fit_rules.effective_clearance(
                    inner["measured"], (inner["model_mu"], inner["model_sigma"]),
                    outer["measured"], (outer["model_mu"], outer["model_sigma"]))
            verdict, advice = fit_rules.classify(lo, mid, hi, j["intent"])
            row.update({"clearance_band": [round(lo, 3), round(mid, 3),
                                           round(hi, 3)],
                        "verdict": verdict, "advice": advice,
                        "inner": sides["inner"], "outer": sides["outer"]})
        results.append(row)
    return results


def press_partners(man, moving):
    out = set()
    for j in man["joints"]:
        if j["intent"] in ("press", "snug"):
            parts = {j["inner"]["part"], j["outer"]["part"]}
            if moving in parts:
                out |= parts - {moving}
    return out


def check_insertions(man, placed, n_steps=21):
    results = []
    static = [n for n in man["parts"] if n not in man["sequence"]]
    for moving in man["sequence"]:
        ins = man["insertions"][moving]
        d, travel = _unit(ins["dir"]), float(ins["travel"])
        mesh = placed[moving]["mesh"]
        pts = np.vstack([mesh.vertices,
                         mesh.sample(max(0, 1200 - len(mesh.vertices)))]
                        if len(mesh.vertices) < 1200 else [mesh.vertices])
        tight = press_partners(man, moving)
        row = {"part": moving, "against": [], "verdict": "PASS"}
        for other in static:
            om = placed[other]["mesh"]
            lo = np.minimum(mesh.bounds[0], mesh.bounds[0] - d * travel) - 1
            hi = np.maximum(mesh.bounds[1], mesh.bounds[1] - d * travel) + 1
            if (om.bounds[1] < lo).any() or (om.bounds[0] > hi).any():
                continue
            pq = trimesh.proximity.ProximityQuery(om)
            worst, worst_s = -np.inf, 0.0
            for s in np.linspace(0.0, 1.0, n_steps):
                offset = -d * travel * (1.0 - s)
                pen = float(pq.signed_distance(pts + offset).max())
                if pen > worst:
                    worst, worst_s = pen, s
            limit = 0.35 if other in tight else 0.10
            ok = worst <= limit
            row["against"].append({"static": other,
                                   "max_penetration": round(worst, 3),
                                   "at_travel_fraction": round(worst_s, 2),
                                   "limit": limit, "ok": ok})
            if not ok:
                row["verdict"] = "FAIL"
        results.append(row)
        static.append(moving)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    base_dir = os.path.dirname(os.path.abspath(a.manifest))
    man = load_manifest(a.manifest)
    placed = place_parts(man, base_dir)

    placement = [{"part": n, "err": round(p["placement_err"], 3),
                  "ok": p["placement_err"] < 0.2}
                 for n, p in placed.items()]
    joints = check_joints(man, placed)
    insertions = check_insertions(man, placed)

    fails = ([p for p in placement if not p["ok"]]
             + [j for j in joints if j["verdict"] == "FAIL"]
             + [i for i in insertions if i["verdict"] == "FAIL"])
    warns = [j for j in joints if j["verdict"] == "WARN"]
    overall = "FAIL" if fails else ("PASS_WITH_WARNINGS" if warns else "PASS")

    report = {"name": man["name"], "printer": man.get("printer", "generic"),
              "calibration": man["calibration"], "overall_verdict": overall,
              "placement": placement, "joints": joints,
              "insertions": insertions}
    out = a.out or os.path.join(base_dir, "assembly_fit.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
