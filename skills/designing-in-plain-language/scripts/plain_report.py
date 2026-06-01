"""Turn a verification.json (and optional structural_review.json) into plain language
for someone new to 3D design.

The verdict in the JSON drives everything. The agent does not pick the colour or
soften a failure: the colour is a deterministic map from the verdict, the wording
comes from fixed per-verdict templates, and a validator rejects any FAIL line that
contains a hedge. Failures are stated with "will"/"won't" and a frequency-format
reason ("about 1 in 5"), because people reason correctly about "1 in 5" and badly
about "0.18" (Gigerenzer & Hoffrage, 1995).

Usage:
    python plain_report.py verification.json [structural_review.json]
"""
from __future__ import annotations
import json
import sys

# The colour is a function of the verdict, never an agent choice.
COLOUR = {"PASS": "🟢", "WARNING": "🟡", "INDETERMINATE": "🟡",
          "METHODS_DISAGREE": "🟡", "FAIL": "🔴", "NOT_RUN": "⚪"}

# A FAIL line containing any of these is a soft-pass in disguise and is rejected.
FORBIDDEN_SOFTENERS = ("may ", "might", "could potentially", "in some cases",
                       "depending on your printer", "should still work",
                       "probably fine", "perhaps")


def _verdict(g: dict) -> str:
    v = g.get("verdict")
    if v:
        return v
    p = g.get("passed")
    if p is True:
        return "PASS"
    if p is None:
        return "INDETERMINATE"
    return "FAIL" if g.get("severity") == "fail" else "WARNING"


def _freq(frac) -> str | None:
    """A '1 in N' frequency phrase from a fraction of the surface."""
    if not frac or frac <= 0:
        return None
    if frac >= 0.5:
        return "most"
    return f"about 1 in {max(2, round(1.0 / frac))}"


def _min_wall_fail(g: dict) -> str:
    cone = g.get("methods", {}).get("cone_sdf", {})
    freq = _freq(cone.get("thin_fraction")) or "some"
    thinnest = g.get("min_wall_mm")
    need = g.get("threshold_mm")
    tail = ""
    if thinnest is not None and need is not None:
        tail = f" The thinnest is {thinnest} mm; it needs to be at least {need} mm."
    return (f"Walls are too thin. {freq.capitalize()} of the walls will print as a single "
            f"fragile strand and snap.{tail} I can thicken them.")


# Per (gate, verdict) plain templates. FAIL templates use will/won't, never a hedge.
def _gate_line(g: dict) -> str | None:
    name, v = g.get("name"), _verdict(g)
    if v == "PASS":
        return None
    if name == "watertight" and v == "FAIL":
        return ("The 3D model isn't fully sealed. There's a gap in its surface that print "
                "software can't read, and I'll close it up.")
    if name == "min_wall":
        if v == "FAIL":
            return _min_wall_fail(g)
        if v == "INDETERMINATE":
            return ("Two checks gave different answers on wall thickness. The shape check "
                    "passed, but the over-estimating check flagged it, so this is borderline "
                    "and worth a closer look before printing.")
        return ("I couldn't measure the wall thickness on this shape, so check it before "
                "printing.")
    if name == "overhangs" and v in ("FAIL", "WARNING"):
        return ("Your design has a steep overhang, a section that leans out over empty space "
                "more than your printer handles cleanly. I can tilt how it prints, chamfer "
                "that edge, or add removable supports.")
    if name == "enclosed_volumes" and v == "FAIL":
        return ("There's a sealed hollow pocket inside with no way out. It will trap air or "
                "material and fail mid-print, and I'll add a small, hidden drain hole.")
    if name == "build_volume" and v == "FAIL":
        return ("Your design is bigger than your printer's bed in at least one direction. I "
                "can shrink it, split it into glue-together pieces, or turn it to fit.")
    return f"There's something to look at with the {name} check, and I can dig in if you want."


def _structural_line(c: dict) -> str | None:
    if _verdict(c) == "PASS":
        return None
    if c.get("name") == "layer_anisotropy":
        return ("The way it's set to print, the main force on it would pull across the layers, "
                "the weaker direction. I can reorient it to be stronger.")
    if c.get("name") == "stress_risers":
        return ("A few sharp inside corners will concentrate stress and can crack. I can round "
                "them so they hold up better.")
    return None


def _validate_no_softeners(line: str, verdict: str):
    if verdict != "FAIL":
        return
    low = line.lower()
    for bad in FORBIDDEN_SOFTENERS:
        if bad in low:
            raise ValueError(f"FAIL line contains a forbidden softener {bad!r}: {line!r}")


def build_report(rep: dict, struct: dict | None = None) -> list[str]:
    items = []
    for g in rep.get("gates", []):
        line = _gate_line(g)
        if line:
            v = _verdict(g)
            _validate_no_softeners(line, v)
            items.append(f"{COLOUR.get(v, '⚪')} {line}")
    if struct:
        for c in struct.get("checks", []):
            line = _structural_line(c)
            if line:
                items.append(f"{COLOUR.get(_verdict(c), '🟡')} {line}")

    lines = []
    if rep.get("manufacturable") and not items:
        lines.append("🟢 Good news: your design looks ready to print. Nothing needs fixing.")
    else:
        lines.append("I checked your design. Here's what I found, in plain terms:")
        lines += ["- " + m for m in items]
        lines.append("Once we sort these, it'll be ready to print."
                     if not rep.get("manufacturable")
                     else "None of these stop you from printing, but they're worth a look.")
    lines.append("")
    lines.append("(Want the technical details behind any of these? Just ask.)")
    return lines


def main():
    rep = json.load(open(sys.argv[1]))
    struct = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else None
    print("\n".join(build_report(rep, struct)))


if __name__ == "__main__":
    main()
