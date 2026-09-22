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
- `model.project.3mf`, only with `--project`: the same geometry as a Bambu Studio project that
  opens in the GUI with the print intent already applied. See "Project export" below.

## How to run
    python scripts/run_handoff.py PART.step \
        --out handoff/ --printer bambu_x1c --nozzle 0.4 --layer-height 0.2 \
        --material PLA --supports auto --brim on \
        --verification verification.json --renders renders/ --spec spec.json

Add `--walls N` to hint a wall-loop count, `--slice` to also produce a sliced
`model.gcode.3mf`, and `--project` to also write `model.project.3mf`. You normally do not
name the binary: the script checks `PATH` and the standard install locations first.
Configured override for this machine: `${user_config.bambu_bin}` (empty means none set,
which is fine). Pass `--bambu-bin <path>` only when that override is set or auto-detection
fails.

## Contract rules (important)
- **print_intent is hints, not commands.** Printer family, nozzle, bed type, layer height,
  supports, brim, and *logical* filament slots are suggestions the downstream agent may
  override. Embedded 3MF presets, when present, are the more reliable source of truth.
- **Never bind physical AMS slots.** Declare logical filament roles (e.g. "primary: PLA") only;
  RFID-driven slot mapping happens at print-send time on the printer, downstream.
- **Do not assume a printer-control path.** Hand off a sliced or sliceable artifact; let the
  printing agent choose LAN+dev mode, Bambu Connect, or SD card.

## Project export: when the user will open the file in Bambu Studio
`model.3mf` is bare geometry, and that is the contract artifact: it carries units, objects,
and positions, and nothing vendor-specific. The GUI, though, opens a bare 3MF with the
notice "The 3mf file has invalid config, load geometry data only", keeps names and
positions, and strips every per-object setting. Nothing in print_intent reaches the
slicer that way; the part prints on whatever presets the app had loaded last. Verified
with Bambu Studio 02.08.02.61: a 4-wall hint sliced at the stock 2 walls (16.7 m of
filament instead of 19.9 m). The headless CLI honours per-object settings in a bare 3MF;
only the GUI drops them.

`--project` closes that gap. It runs `model.3mf` through the Bambu Studio CLI with the
bundled machine, process, and filament presets that match print_intent, writes the hints
into the process preset as real overrides, exports a project (no slicing), and marks the
overridden keys as user changes in `Metadata/project_settings.config`. The GUI opens the
result as one of its own projects, with no notice, nothing to set, and the overrides shown
as modified settings. The mapping:

| print_intent | Bambu preset |
|---|---|
| `printer_family` + `nozzle_mm` | machine preset, e.g. `Bambu Lab X1 Carbon 0.4 nozzle`; `generic` uses the X1C |
| `layer_height_mm` | the sibling process preset at that height, else the default with `layer_height` overridden |
| `filament_slots_logical[0].material` | the Bambu Basic, Bambu, or Generic filament preset for that machine, else the default with a note |
| `supports` off / auto / tree / normal | `enable_support` and `support_type` |
| `brim` on / off / outer / inner / both | `brim_type` |
| `bed_type` textured_pei / cool / engineering / high_temp / supertack | `curr_bed_type` |
| `walls` (`--walls N`) | `wall_loops` |

A value with no mapping is left at the preset default and named in the result's `note`;
nothing is guessed. Prusa families are refused (the note says so) because the file is a
Bambu Studio project. The print pose from orienting-for-fdm is kept (`--orient 0`); a lone
part is arranged onto the plate centre, since unarranged it sits at the bed corner. For a
hand-laid plate with several objects at deliberate positions, pass `--keep-layout`.

Two rules for a multi-object plate, whichever export you use: give every copy its own
`<object>` (several `<build><item>`s sharing one object are split into N objects on import,
and the name and settings go to the first only), and put plate positions in the item
transform with the mesh centred on the origin, since baked-in vertex positions are
re-centred on import.

**Do not redistribute `model.project.3mf` casually.** It embeds Bambu's machine, process,
and filament preset data, plus the app's slicing metadata. Hand it to the person printing,
keep it out of repositories or part libraries that promise bare geometry or vendor-free
files, and treat `model.3mf` plus `manifest.json` as the artifact that travels. When the
file was produced, provenance hashes it alongside the bare 3MF.

To confirm the settings really arrived, slice the same part twice in the GUI, once from the
bare `model.3mf` and once from the project, and compare the filament estimate. A wall-count
change moves it by tens of percent; identical numbers mean the override was dropped.

## Slicing notes
The Bambu Studio CLI is the slicing engine. Always set a per-plate timeout (`--mstpp`) and a
sandboxed temp dir, because pathological meshes can hang it and it writes large temp files. A
slice against a 3MF with embedded presets is far more reliable than STL + external preset JSON,
which often falls back to defaults with unknown filament.

## Dependencies
`pip install "build123d>=0.10" trimesh numpy` plus, for `--slice` and `--project`, a local
Bambu Studio install exposing its CLI. Auto-detection covers the standard macOS and Linux install paths;
set the plugin's `bambu_bin` option (`/plugin configure printagent`) for anything else.

If a script reports that packages are missing, do not hand the user pip commands and do not try to fix an import error by hand. Run the plugin's bootstrap, which builds a private environment and records it so every skill finds it with nothing to activate:

    python3 <plugin root>/scripts/bootstrap_env.py --check
    python3 <plugin root>/scripts/bootstrap_env.py --install
