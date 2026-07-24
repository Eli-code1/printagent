"""Hand-crank desk fan — SNAP-TOGETHER (multi-part), single-stage spur-gear step-up.

Five printed parts: a reclining base, a spoked hand-wheel, an impeller-pinion, and
two press-in pivot pins. Assembly: set a gear over a base hole, push a pin down
through the gear into the hole. The pin's lower section press-fits into the base;
the gear spins free on the pin's journal, held captive under the head. ~10 seconds,
no glue, no floating islands.

Each part prints flat in its own orientation (gears lie down -> crisp teeth; pins
head-down; base on its wedge). The gears step the crank speed up ~4x.

Module-level objects:
  base, wheel, pinion, pin_a, pin_b : reclined, in their ASSEMBLED positions
  part        : the assembled compound (for rendering / fit checks)
  print_plate : the five parts laid out flat on the bed, ready to slice

z=0 is the print bed, +Z is the build direction. build123d >= 0.10, algebra mode.
"""
from __future__ import annotations
import math
from build123d import (
    Align, Axis, Box, Compound, Cylinder, GeomType, Plane, Polygon, Pos,
    Rot, extrude, fillet, revolve,
)

# ------------------------------------------------------------------- gears
M = 1.5
Z_WHEEL = 48
Z_PINION = 12
CD = M * (Z_WHEEL + Z_PINION) / 2.0     # center distance = 45 mm
FACE = 8.0                              # gear thickness

# ------------------------------------------------------------------- pivot fits
PIN_SHAFT_R = 2.55     # D5.1 shaft (journal + press section share one diameter)
BASE_HOLE_R = 2.50     # D5.0 base hole -> ~0.1 mm interference, pin press-fits
GEAR_BORE_R = 2.75     # D5.5 gear bore -> 0.4 mm dia clearance, spins on the shaft
PIN_HEAD_R = 3.30      # D6.6 head, retains the gear (> bore)
PIN_HEAD_H = 2.0
PRESS_DEPTH = 6.0      # length of pin that presses into the base
AXIAL_PLAY = 0.6       # journal a touch longer than the gear so it isn't clamped
BOSS_R = 5.5           # solid boss around each hole, gives press material

# ------------------------------------------------------------------- base / deck
BASE_T = 3.0
GEAR_Z0 = BASE_T       # gear sits on the deck top
GEAR_Z1 = GEAR_Z0 + FACE

WHEEL_HUB_R = 8.0
WHEEL_RIM_INNER = M * Z_WHEEL / 2 - 1.25 * M - 1.0
N_SPOKES = 5
SPOKE_W = 5.0
SPOKE_OFFSET = 36.0
KNOB_R = 3.5
KNOB_H = 12.0
KNOB_AT_R = 30.0

PINION_HUB_R = 6.0
PINION_HUB_TOP = GEAR_Z0 + 21.0
N_BLADES = 5
BLADE_T = 2.6
EPS = 0.02

RECLINE_DEG = 18.0
TILT_LIFT = 16.0
BIG = 1000.0


def spur_gear(module, teeth, face, phase_deg=0.0, tooth_frac=0.30):
    """Simplified spur gear: solid disc to the root + N angular tooth wedges with
    chamfered addendum corners. Thin teeth (0.30 of pitch) give ~0.36 mm mesh
    backlash so the pair turns freely. Built on z=0..face, no bore."""
    pitch_r = module * teeth / 2.0
    r_add = pitch_r + module
    r_root = pitch_r - 1.25 * module
    pitch_ang = 360.0 / teeth
    tooth_ang = tooth_frac * pitch_ang

    core = Cylinder(r_root + EPS, face, align=(Align.CENTER, Align.CENTER, Align.MIN))
    ri = r_root - EPS
    c = min(0.6, face * 0.3, (r_add - ri) * 0.3)
    prof = Plane.XZ * Polygon(
        (ri, 0.0), (r_add - c, 0.0), (r_add, c),
        (r_add, face - c), (r_add - c, face), (ri, face), align=None)
    tooth = revolve(prof, axis=Axis.Z, revolution_arc=tooth_ang)
    gear = core
    for i in range(teeth):
        gear += Rot(0, 0, phase_deg + i * pitch_ang - tooth_ang / 2.0) * tooth
    return gear


def gear_bore(part, x=0.0, z0=-1.0, z1=60.0):
    return part - Pos(x, 0, z0) * Cylinder(
        GEAR_BORE_R, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


# ------------------------------------------------------------------- wheel (free part)
def build_wheel():
    g = spur_gear(M, Z_WHEEL, FACE, phase_deg=0.0)
    web = (Cylinder(WHEEL_RIM_INNER, FACE, align=(Align.CENTER, Align.CENTER, Align.MIN))
           - Cylinder(WHEEL_HUB_R, FACE, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    spoke_len = WHEEL_RIM_INNER - WHEEL_HUB_R + 2 * EPS
    spoke_mid = (WHEEL_HUB_R + WHEEL_RIM_INNER) / 2.0
    spokes = None
    for k in range(N_SPOKES):
        s = Rot(0, 0, SPOKE_OFFSET + k * 360.0 / N_SPOKES) * Pos(spoke_mid, 0, 0) * Box(
            spoke_len, SPOKE_W, FACE, align=(Align.CENTER, Align.CENTER, Align.MIN))
        spokes = s if spokes is None else spokes + s
    g -= (web - spokes)
    g = gear_bore(g, 0.0, 0.0, FACE)
    g = Pos(0, 0, GEAR_Z0) * g
    knob = Pos(-KNOB_AT_R, 0, GEAR_Z1 - EPS) * Cylinder(
        KNOB_R, KNOB_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    g += knob
    try:
        g = fillet(g.edges().filter_by(GeomType.CIRCLE).sort_by(Axis.Z)[-1],
                   radius=min(1.4, KNOB_R - 0.1))
    except Exception:
        pass
    return g


# ------------------------------------------------------------------- pinion + impeller (free part)
def one_blade():
    # blades are ELEVATED so the swept disc clears the wheel top (which is at
    # GEAR_Z1); bottom edge rises ~30 deg so it self-supports off the hub.
    z = GEAR_Z0 + 10.0            # blade bottom, well above the wheel top (GEAR_Z1)
    prof = Plane.XZ * Polygon(
        (PINION_HUB_R - EPS, z),
        (20.0, z + 8.0),
        (22.0, z + 10.0),
        (22.0, z + 14.0),
        (20.0, z + 16.0),
        (PINION_HUB_R - EPS, z + 6.0), align=None)
    return extrude(prof, amount=BLADE_T / 2, both=True)


def build_pinion_rotor():
    g = Pos(0, 0, GEAR_Z0) * spur_gear(M, Z_PINION, FACE, phase_deg=180.0 / Z_PINION)
    hub = Pos(0, 0, GEAR_Z0) * Cylinder(
        PINION_HUB_R, PINION_HUB_TOP - GEAR_Z0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    rotor = g + hub
    for k in range(N_BLADES):
        rotor += Rot(0, 0, k * 360.0 / N_BLADES) * one_blade()
    # journal bore (D5.5) through the gear; spins on the pin shaft
    rotor -= Pos(0, 0, GEAR_Z0 - EPS) * Cylinder(
        GEAR_BORE_R, FACE + EPS, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # counterbore (clears the pin head) up through the hub; the D5.5->counterbore
    # shoulder at the gear top catches the head and keeps the rotor captive
    rotor -= Pos(0, 0, GEAR_Z1) * Cylinder(
        PIN_HEAD_R + 0.1, PINION_HUB_TOP - GEAR_Z1 + EPS,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos(CD, 0, 0) * rotor


# ------------------------------------------------------------------- pivot pin (printed part)
def build_pin():
    """A press-in pivot: head + shaft. Lower PRESS_DEPTH presses into the base hole;
    the journal above (length = gear face + play) is what the gear spins on; the head
    keeps the gear captive. Built head-up on z=0; the plate lays it head-down to print."""
    journal = FACE + AXIAL_PLAY
    shaft = Cylinder(PIN_SHAFT_R, PRESS_DEPTH + journal,
                     align=(Align.CENTER, Align.CENTER, Align.MIN))
    head = Pos(0, 0, PRESS_DEPTH + journal) * Cylinder(
        PIN_HEAD_R, PIN_HEAD_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    pin = shaft + head
    try:  # round the head top
        pin = fillet(pin.edges().filter_by(GeomType.CIRCLE).sort_by(Axis.Z)[-1], radius=0.8)
    except Exception:
        pass
    return pin


def seat_pin(x):
    """Place a pin in its assembled spot: press section sunk into the base, journal
    spanning the gear, head above. Pin z=0 is the bottom of the press section, which
    sits PRESS_DEPTH below the deck top."""
    return Pos(x, 0, GEAR_Z0 - PRESS_DEPTH) * build_pin()


# ------------------------------------------------------------------- base (printed part)
def build_base():
    x0, x1 = -42.5, 74.0
    y_half = 42.5
    cx = (x0 + x1) / 2.0
    plate = Pos(cx, 0, BASE_T / 2.0) * Box(x1 - x0, 2 * y_half, BASE_T)
    try:
        plate = fillet(plate.edges().filter_by(Axis.Z), radius=6.0)
    except Exception:
        pass
    under = Pos(cx, 0, 0.5) * Box(x1 - x0, 2 * y_half, BIG,
                                  align=(Align.CENTER, Align.CENTER, Align.MAX))
    # lighten into a ribbed shell
    wall, rib, cell, roof = 2.4, 2.0, 28.0, 1.2
    xi0, xi1, yi0, yi1 = x0 + wall, x1 - wall, -y_half + wall, y_half - wall
    pockets = None
    xx = xi0
    while xx < xi1 - 4.0:
        xw = min(cell, xi1 - xx)
        yy = yi0
        while yy < yi1 - 4.0:
            yw = min(cell, yi1 - yy)
            pk = Pos(xx + xw / 2.0, yy + yw / 2.0, -roof) * Box(
                xw, yw, BIG, align=(Align.CENTER, Align.CENTER, Align.MAX))
            pockets = pk if pockets is None else pockets + pk
            yy += cell + rib
        xx += cell + rib
    if pockets is not None:
        under = under - pockets
    base = plate + under
    # solid bosses with press-fit holes at each pivot
    for x in (0.0, CD):
        boss = Pos(x, 0, -8.0) * Cylinder(BOSS_R, BASE_T + 8.0,
                                          align=(Align.CENTER, Align.CENTER, Align.MIN))
        base += boss
    for x in (0.0, CD):
        hole = Pos(x, 0, GEAR_Z0 - (PRESS_DEPTH + 1.0)) * Cylinder(
            BASE_HOLE_R, PRESS_DEPTH + 1.0 + EPS, align=(Align.CENTER, Align.CENTER, Align.MIN))
        base -= hole
    return base


def recline(body):
    return Pos(0, 0, TILT_LIFT) * (Rot(RECLINE_DEG, 0, 0) * body)


# ------------------------------------------------------------------- assembly (reclined, for view/fit)
_base_flat = build_base()
base = recline(_base_flat)
base = base & Pos(0, 0, 0) * Box(BIG, BIG, BIG, align=(Align.CENTER, Align.CENTER, Align.MIN))
wheel = recline(build_wheel())
pinion = recline(build_pinion_rotor())
pin_a = recline(seat_pin(0.0))
pin_b = recline(seat_pin(CD))
for _body, _nm in zip((base, wheel, pinion, pin_a, pin_b),
                      ("base", "wheel", "pinion", "pin", "pin")):
    _body.label = _nm
part = Compound(children=[base, wheel, pinion, pin_a, pin_b])
part.label = "hand_crank_fan"


# ------------------------------------------------------------------- print plate (flat, separate)
def _drop(body, dz):
    return Pos(0, 0, dz) * body


def build_plate():
    # base: already sits on its wedge bottom at z=0 after recline+cut
    b = base
    # wheel & pinion: flat (pre-recline), gear bottom dropped to the bed
    w = _drop(build_wheel(), -GEAR_Z0)
    p = _drop(build_pinion_rotor(), -GEAR_Z0)
    # pins: head-down on the bed (flip 180 about X), shaft up
    pin_flat = Rot(180, 0, 0) * build_pin()
    pin_flat = Pos(0, 0, -pin_flat.bounding_box().min.Z) * pin_flat
    # lay out non-overlapping on the bed
    items = [Pos(60, 55, 0) * b,
             Pos(60, 165, 0) * w,
             Pos(150, 165, 0) * p,
             Pos(140, 60, 0) * pin_flat,
             Pos(158, 60, 0) * pin_flat]
    # named so the STEP imports into CAD (Onshape etc.) as named parts; the two
    # pins are the same shape, which STEP dedupes to one product, so one name
    for body, nm in zip(items, ("base", "wheel", "pinion", "pin", "pin")):
        body.label = nm
    return Compound(children=items)


print_plate = build_plate()


if __name__ == "__main__":
    for name, body in [("base", base), ("wheel", wheel), ("pinion", pinion),
                       ("pin_a", pin_a)]:
        print(f"{name}: valid={body.is_valid} solids={len(body.solids())} vol={body.volume:.0f}")
    pb = print_plate.bounding_box()
    print(f"plate bbox: {[round(v,1) for v in pb.size]}  x:[{pb.min.X:.0f},{pb.max.X:.0f}] "
          f"y:[{pb.min.Y:.0f},{pb.max.Y:.0f}]")
