---
name: slicing-handoff-bambu
description: >-
  Packages a verified FDM part into the handoff artifact for printing: exports a millimetre
  3MF plus an archival STEP, gathers the verification report and renders, and writes a
  manifest.json declaring geometry, print intent (as hints), verification results, and
  provenance. Optionally slices with the Bambu Studio CLI. Use when exporting a part for
  printing, preparing a 3MF, slicing, or handing a finished design to a Bambu Lab printer or a
  downstream printing agent. Treats print intent as overridable hints and never binds physical
  AMS slots.
---

# Slicing and handoff to Bambu

This skill produces the contract artifact that crosses the boundary from the design project to
the printing project. It assembles a self-describing directory; it does not own the printer.
Slicing is included and is unaffected by Bambu's firmware lockdown; *starting a print* is
deliberately out of scope, because the Authorization Control System constrains it to LAN +
developer mode, Bambu Connect, or SD-card delivery, a choice the downstream printing agent
owns, not this one.

## What it produces
A handoff directory containing:
- `model.3mf`, millimetre geometry for the slicer (3MF carries units and survives transport;
  preferred over STL).
- `model.step`, lossless B-rep archive for CAD round-trip.
- `verification.json`, the manufacturability gate's report (gates passed/failed/warnings).
- `renders/`, multi-view PNGs, if provided.
- `provenance.json`, file hashes, timestamps, and the source spec reference for auditability.
- `manifest.json`, the contract: geometry block, print_intent (hints), verification, provenance.

## How to run
    python scripts/run_handoff.py PART.step \
        --out handoff/ --printer bambu_x1c --nozzle 0.4 --layer-height 0.2 \
        --material PLA --supports auto --brim on \
        --verification verification.json --renders renders/ --spec spec.json

Add `--slice` with `--bambu-bin /path/to/bambu-studio` to also produce a sliced
`model.gcode.3mf`.

## Contract rules (important)
- **print_intent is hints, not commands.** Printer family, nozzle, bed type, layer height,
  supports, brim, and *logical* filament slots are suggestions the downstream agent may
  override. Embedded 3MF presets, when present, are the more reliable source of truth.
- **Never bind physical AMS slots.** Declare logical filament roles (e.g. "primary: PLA") only;
  RFID-driven slot mapping happens at print-send time on the printer, downstream.
- **Do not assume a printer-control path.** Hand off a sliced or sliceable artifact; let the
  printing agent choose LAN+dev mode, Bambu Connect, or SD card.

## Slicing notes
The Bambu Studio CLI is the slicing engine. Always set a per-plate timeout (`--mstpp`) and a
sandboxed temp dir, because pathological meshes can hang it and it writes large temp files. A
slice against a 3MF with embedded presets is far more reliable than STL + external preset JSON,
which often falls back to defaults with unknown filament.

## Dependencies
`pip install "build123d>=0.10" trimesh numpy` plus, for `--slice`, a local Bambu Studio
install exposing its CLI.
