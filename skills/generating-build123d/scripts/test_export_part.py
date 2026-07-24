"""Prove exported STEP files carry real product names, so CAD imports (Onshape,
Fusion, FreeCAD) show named parts instead of "Part 1"/"COMPOUND". Run on any
change to export_part.py.

Usage:
    python test_export_part.py
"""
import os
import re
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from build123d import Box, Compound, Cylinder, Pos  # noqa: E402
from export_part import export_part                  # noqa: E402


def products(step_path):
    """The set of PRODUCT names written to the STEP file."""
    with open(step_path) as f:
        return set(re.findall(r"PRODUCT\('([^']*)'", f.read()))


def main():
    tmp = tempfile.mkdtemp(prefix="export_part_")
    fails = 0

    def check(label, cond, detail):
        nonlocal fails
        fails += not cond
        print(f"{'ok ' if cond else 'XX '}{label}: {detail}")

    # 1. Unlabeled part: product name defaults to the stem's basename.
    p = export_part(Box(10, 10, 5), os.path.join(tmp, "widget"), also_stl=False)
    check("default_name_from_stem", products(p) == {"widget"}, products(p))

    # 2. Explicit name wins over the stem.
    p = export_part(Box(10, 10, 5), os.path.join(tmp, "out"), also_stl=False,
                    name="bracket_v1")
    check("explicit_name", products(p) == {"bracket_v1"}, products(p))

    # 3. A label already on the part is kept.
    b = Box(10, 10, 5)
    b.label = "hub"
    p = export_part(b, os.path.join(tmp, "out2"), also_stl=False)
    check("existing_label_kept", products(p) == {"hub"}, products(p))

    # 4. Compound with unlabeled children: each child gets a derived name, so a
    #    multi-body import still yields individually named parts.
    asm = Compound(children=[Box(10, 10, 5), Pos(0, 0, 10) * Cylinder(3, 8)])
    p = export_part(asm, os.path.join(tmp, "fan"), also_stl=False)
    check("compound_children_named",
          products(p) == {"fan", "fan_1", "fan_2"}, products(p))

    # 5. Compound with labeled children: labels pass through untouched.
    c1 = Box(10, 10, 5)
    c1.label = "base_plate"
    c2 = Pos(0, 0, 10) * Cylinder(3, 8)
    c2.label = "hub"
    asm = Compound(children=[c1, c2])
    asm.label = "fan_assembly"
    p = export_part(asm, os.path.join(tmp, "out3"), also_stl=False)
    check("labeled_children_kept",
          products(p) == {"fan_assembly", "base_plate", "hub"}, products(p))

    print(f"\n{5 - fails} of 5 passing")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
