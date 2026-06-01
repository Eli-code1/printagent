"""Run the min-wall gate against the golden corpus; exit nonzero on any mismatch.

Usage:
    python run_evals.py
This is the regression harness for the gate. Run it on every change to gate
logic. The cube must pass and the sub-threshold walls must fail, deterministically.
"""
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "scripts"))

from build123d import export_stl                     # noqa: E402
import golden_set                                     # noqa: E402
from geometry_io import load_mesh, sanitize           # noqa: E402
from check_min_wall import check_min_wall             # noqa: E402


def main():
    tmp = tempfile.mkdtemp(prefix="minwall_evals_")
    rows, fails = [], 0
    for name, builder, T, expected in golden_set.CASES:
        stl = os.path.join(tmp, name + ".stl")
        export_stl(builder(), stl)
        mesh, _ = sanitize(load_mesh(stl))
        res = check_min_wall(mesh, T)
        got = res["verdict"]
        ok = got == expected
        fails += not ok
        cone = res["methods"]["cone_sdf"]
        rows.append(("ok " if ok else "XX ", name, T, expected, got,
                     res.get("min_wall_mm"), cone.get("thin_fraction")))

    w = max(len(r[1]) for r in rows)
    print(f"{'':3}{'case':<{w}}  T     expect  got           min_mm  thin_frac")
    for flag, name, T, exp, got, mm, tf in rows:
        print(f"{flag}{name:<{w}}  {T:<4}  {exp:<6}  {got:<12}  {mm}    {tf}")
    print(f"\n{len(rows) - fails}/{len(rows)} cases match expected")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
