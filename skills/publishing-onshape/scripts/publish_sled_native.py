"""Publish the Apollo sled to Onshape as a NATIVE feature tree.

Creates a document and builds the sled as ordinary Onshape features - real
sketches and extrudes the user can click and edit like hand-modeled work, no
custom-feature black box. All sketches sit on the default Top plane so no
face-id discovery is needed; the blind tripod socket comes from a through-bore
plus a 2 mm cap re-added at the top (same resulting solid as sled.py, minus
chamfers and the modeled thread, which stay in the print pipeline).

Frame: z=0 is the plate TOP (fan base plane); the part hangs downward, ribs up.

Usage:
    python publish_sled_native.py [--name "Apollo sled (native)"] [--dry-run]
"""
from __future__ import annotations
import argparse
import re

from onshape_client import calls_this_run, lifetime_calls, request

MM = 0.001  # sketch geometry is in meters

# mirrored from parts/apollo-fan-tripod-sled (coupon v6 fit + sled.py)
P = dict(
    plate_w=56.0, plate_d=44.0, plate_t=3.0,
    rib_front_y=18.0, rib_len=22.0, rib_h=2.0,
    slot_front_w=4.0, slot_peak_d=8.85, slot_peak_w=4.65, slot_taper=0.10,
    rib_gap_at_peak=40.2, clearance_side=0.15,
    notch_w=8.0, notch_d=2.0,
    boss_d=16.0, boss_h=7.0, boss_y=-3.85,
    bore_d=6.65, socket_cap=2.0,
)


def slot_width(d: float) -> float:
    if d <= P["slot_peak_d"]:
        return P["slot_front_w"] + (P["slot_peak_w"] - P["slot_front_w"]) * d / P["slot_peak_d"]
    return P["slot_peak_w"] - P["slot_taper"] * (d - P["slot_peak_d"])


def rib_points(side: int) -> list[tuple[float, float]]:
    """Six-point kite outline for one rib (mm, plate coordinates)."""
    c = P["clearance_side"]
    peak_w = slot_width(P["slot_peak_d"]) - 2 * c
    cx = side * (P["rib_gap_at_peak"] / 2.0 + peak_w / 2.0)
    pts = []
    stations = [0.0, P["slot_peak_d"], P["rib_len"]]
    for d in stations:
        w = slot_width(d) - 2 * c
        pts.append((cx + side * w / 2.0, P["rib_front_y"] - d))
    for d in reversed(stations):
        w = slot_width(d) - 2 * c
        pts.append((cx - side * w / 2.0, P["rib_front_y"] - d))
    return pts


# ---------------------------------------------------------------- BTM builders
def line_entities(prefix: str, pts_mm: list[tuple[float, float]]) -> list[dict]:
    """Closed polyline as unconstrained sketch line segments."""
    out = []
    n = len(pts_mm)
    for i in range(n):
        x0, y0 = pts_mm[i]
        x1, y1 = pts_mm[(i + 1) % n]
        eid = f"{prefix}.{i}"
        out.append({
            "btType": "BTMSketchCurveSegment-155",
            "entityId": eid,
            "startPointId": eid + ".start",
            "endPointId": eid + ".end",
            "startParam": 0.0,
            "endParam": 1.0,
            "geometry": {
                "btType": "BTCurveGeometryLine-117",
                "pntX": x0 * MM, "pntY": y0 * MM,
                "dirX": (x1 - x0) * MM, "dirY": (y1 - y0) * MM,
            },
        })
    return out


def rect_entities(prefix: str, x0, y0, x1, y1) -> list[dict]:
    return line_entities(prefix, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def circle_entity(prefix: str, cx, cy, r) -> list[dict]:
    return [{
        "btType": "BTMSketchCurve-4",
        "entityId": prefix,
        "centerId": prefix + ".center",
        "geometry": {
            "btType": "BTCurveGeometryCircle-115",
            "xCenter": cx * MM, "yCenter": cy * MM, "radius": r * MM,
            "xDir": 1.0, "yDir": 0.0, "clockwise": False,
        },
    }]


def sketch_feature(name: str, plane_id: str, entities: list[dict]) -> dict:
    return {
        "btType": "BTMSketch-151",
        "featureType": "newSketch",
        "name": name,
        "parameters": [{
            "btType": "BTMParameterQueryList-148",
            "parameterId": "sketchPlane",
            "queries": [{"btType": "BTMIndividualQuery-138",
                         "queryString": f'query=qCreatedBy(makeId("{plane_id}"), EntityType.FACE);'}],
        }],
        "entities": entities,
        "constraints": [],
    }


def extrude_feature(name: str, sketch_fid: str, depth_mm: float,
                    operation: str, down: bool, scope_fid: str | None = None) -> dict:
    """scope_fid: featureId of the body-creating feature (e.g. the base extrude).
    Booleans (ADD/REMOVE) get an explicit merge scope on that body instead of
    'merge with all', so extra bodies added later can never be caught by a cut."""
    params = [
        {"btType": "BTMParameterEnum-145", "parameterId": "bodyType",
         "value": "SOLID", "enumName": "ExtendedToolBodyType"},
        {"btType": "BTMParameterEnum-145", "parameterId": "operationType",
         "value": operation, "enumName": "NewBodyOperationType"},
        {"btType": "BTMParameterQueryList-148", "parameterId": "entities",
         "queries": [{"btType": "BTMIndividualSketchRegionQuery-140",
                      "featureId": sketch_fid}]},
        {"btType": "BTMParameterEnum-145", "parameterId": "endBound",
         "value": "BLIND", "enumName": "BoundingType"},
        {"btType": "BTMParameterQuantity-147", "parameterId": "depth",
         "expression": f"{depth_mm} mm"},
        {"btType": "BTMParameterBoolean-144", "parameterId": "oppositeDirection",
         "value": bool(down)},
    ]
    if operation != "NEW" and scope_fid:
        params += [
            {"btType": "BTMParameterBoolean-144", "parameterId": "defaultScope",
             "value": False},
            {"btType": "BTMParameterQueryList-148", "parameterId": "booleanScope",
             "queries": [{"btType": "BTMIndividualQuery-138",
                          "queryString":
                          f'query=qCreatedBy(makeId("{scope_fid}"), EntityType.BODY);'}]},
        ]
    return {
        "btType": "BTMFeature-134",
        "featureType": "extrude",
        "name": name,
        "parameters": params,
        "returnAfterSubfeatures": False,
        "suppressed": False,
    }


# ---------------------------------------------------------------- publish flow
def add_feature(did: str, wid: str, eid: str, feature: dict) -> str:
    r = request("POST", f"/api/v6/partstudios/d/{did}/w/{wid}/e/{eid}/features",
                {"btType": "BTFeatureDefinitionCall-1406", "feature": feature})
    fid = r.get("feature", {}).get("featureId", "")
    # the POST response already carries this feature's regen state - checking it
    # here saves a follow-up GET and fails fast instead of stacking onto a wreck
    status = (r.get("featureState") or {}).get("featureStatus", "OK")
    print(f"  + {feature['name']} (featureId={fid}, {status})")
    if status not in ("OK", ""):
        raise SystemExit(f"feature '{feature['name']}' failed to regenerate: {status}")
    return fid


def volume_mm3(did: str, wid: str, eid: str) -> float:
    r = request("GET", f"/api/v10/partstudios/d/{did}/w/{wid}/e/{eid}/massproperties")
    body = (r.get("bodies") or {}).get("-all-") or {}
    vol = body.get("volume") or [0]
    return vol[0] / (MM ** 3)


def build_plan(plane_id: str) -> list[tuple[str, dict, float | None, str, bool]]:
    """(kind, sketch-or-none, depth, operation, down) pairs, in order."""
    hw, hd = P["plate_w"] / 2, P["plate_d"] / 2
    plate_sk = sketch_feature("Plate profile", plane_id,
                              rect_entities("plate", -hw, -hd, hw, hd))
    ribs_sk = sketch_feature("Rib kites", plane_id,
                             line_entities("ribR", rib_points(+1)) +
                             line_entities("ribL", rib_points(-1)))
    boss_sk = sketch_feature("Boss circle", plane_id,
                             circle_entity("boss", 0.0, P["boss_y"], P["boss_d"] / 2))
    notch_sk = sketch_feature("Front notch", plane_id,
                              rect_entities("notch", -P["notch_w"] / 2, hd - P["notch_d"],
                                            P["notch_w"] / 2, hd + 0.6))
    bore_sk = sketch_feature("Tripod bore", plane_id,
                             circle_entity("bore", 0.0, P["boss_y"], P["bore_d"] / 2))
    stack = P["plate_t"] + P["boss_h"]
    return [
        ("Plate", plate_sk, P["plate_t"], "NEW", True),
        ("Ribs", ribs_sk, P["rib_h"], "ADD", False),
        ("Boss", boss_sk, stack, "ADD", True),
        ("Notch cut", notch_sk, P["plate_t"] + 0.5, "REMOVE", True),
        ("Bore cut", bore_sk, stack + 5.0, "REMOVE", True),
        ("Socket cap", bore_sk, P["socket_cap"], "ADD", True),
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="Apollo sled (native)")
    ap.add_argument("--url", help="existing document URL to build into "
                                  "(.../documents/DID/w/WID/e/EID); skips creation")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    if a.dry_run:
        plan = build_plan("JDC")
        for name, sk, depth, op, down in plan:
            ents = len(sk["entities"])
            print(f"{name}: sketch '{sk['name']}' ({ents} entities) -> "
                  f"extrude {op} {depth} mm {'down' if down else 'up'}")
        print("dry-run OK")
        return

    if a.url:
        m = re.search(r"documents/(\w+)/w/(\w+)/e/(\w+)", a.url)
        if not m:
            raise SystemExit("--url must look like .../documents/DID/w/WID/e/EID")
        did, wid, eid = m.groups()
    else:
        print("creating document...")
        doc = request("POST", "/api/v10/documents", {"name": a.name, "isPublic": False})
        did = doc["id"]
        wid = doc["defaultWorkspace"]["id"]
        elems = request("GET", f"/api/v10/documents/d/{did}/w/{wid}/elements")
        eid = next(e["id"] for e in elems if e.get("elementType") == "PARTSTUDIO")
    url = f"https://cad.onshape.com/documents/{did}/w/{wid}/e/{eid}"
    print(f"document: {url}")

    plane_id = "Top"   # referenced by feature name via qCreatedBy(makeId(...))

    sketch_fids: dict[int, str] = {}
    base_fid: str | None = None       # the NEW extrude's body anchors merge scope
    for name, sk, depth, op, down in build_plan(plane_id):
        key = id(sk)
        if key not in sketch_fids:
            sketch_fids[key] = add_feature(did, wid, eid, sk)
        fid = add_feature(did, wid, eid,
                          extrude_feature(name, sketch_fids[key], depth, op, down,
                                          scope_fid=base_fid))
        if op == "NEW" and base_fid is None:
            base_fid = fid

    vol = volume_mm3(did, wid, eid)
    print(f"all features OK; volume {vol:.0f} mm^3 (expected ~8810)")
    print(f"API calls: {calls_this_run()} this run, {lifetime_calls()} since counter start")
    print(url)


if __name__ == "__main__":
    main()
