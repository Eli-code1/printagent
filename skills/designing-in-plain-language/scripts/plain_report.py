"""Turn a verification.json (and optional structural_review.json) into plain language for
someone new to 3D design. Leads with what each issue means and why it matters, then offers a
plain fix. Hides coordinates, raw thresholds, and JSON field names.

Usage:
    python plain_report.py verification.json [structural_review.json]
"""
from __future__ import annotations
import json
import sys


def plain_gate(g: dict):
    name, passed = g.get("name"), g.get("passed")
    if passed is True:
        return None
    if name == "watertight" and passed is False:
        return ("The 3D model isn't fully sealed — there's a gap or hole in its surface that "
                "print software can't read. I'll close it up.")
    if name == "min_wall":
        if passed is None:
            return ("I couldn't fully check how thick the walls are on this shape — worth a "
                    "closer look before printing.")
        return ("Part of your design is too thin to print reliably. Thin spots come out "
                "fragile or don't print at all. I can thicken them — want me to?")
    if name == "overhangs" and passed is False:
        return ("Your design has a steep overhang — a section that leans out over empty space "
                "more than your printer handles cleanly. I can tilt how it's printed, round or "
                "angle that edge, or add removable scaffolding. Want me to pick the cleanest?")
    if name == "enclosed_volumes" and passed is False:
        return ("There's a sealed hollow pocket inside with no way out, which can trap air or "
                "material and fail mid-print. I'll add a small, hidden drain hole.")
    if name == "build_volume" and passed is False:
        return ("Your design is bigger than your printer's bed in at least one direction. I can "
                "shrink it, split it into glue-together pieces, or turn it to fit. What works?")
    return f"There's something to look at with '{name}'. I can dig in if you'd like."


def plain_structural(s: dict):
    out = []
    for c in s.get("checks", []):
        if c.get("passed") is not False:
            continue
        if c.get("name") == "layer_anisotropy":
            out.append("The way it's set to print, the main force on it would pull across the "
                       "layers — the weaker direction. I can reorient it to be stronger. Worth "
                       "doing?")
        elif c.get("name") == "stress_risers":
            out.append("A few sharp inside corners could crack under stress. I can round them "
                       "slightly so they hold up better.")
    return out


def main():
    rep = json.load(open(sys.argv[1]))
    issues = [m for m in (plain_gate(g) for g in rep.get("gates", [])) if m]

    lines = []
    if rep.get("manufacturable") and not issues:
        lines.append("Good news — your design looks ready to print. Nothing needs fixing.")
    else:
        lines.append("I checked your design. Here's what I found, in plain terms:")
        lines += ["- " + m for m in issues]
        lines.append("Once we sort these, it'll be ready to print."
                     if not rep.get("manufacturable")
                     else "None of these stop you from printing, but they're worth a look.")

    if len(sys.argv) > 2:
        lines += ["- " + m for m in plain_structural(json.load(open(sys.argv[2])))]

    lines.append("")
    lines.append("(Want the technical details behind any of these? Just ask.)")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
