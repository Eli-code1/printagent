# Handoff contract

## manifest.json schema
```json
{
  "geometry": {
    "units": "mm",
    "bbox_mm": [x, y, z],
    "watertight": true,
    "n_faces": 0
  },
  "print_intent": {
    "_note": "hints, overridable; embedded 3MF presets win if present",
    "printer_family": "bambu_x1c",
    "nozzle_mm": 0.4,
    "layer_height_mm": 0.2,
    "bed_type": "textured_pei",
    "supports": "auto",
    "brim": "on",
    "walls": 4,
    "filament_slots_logical": [{"role": "primary", "material": "PLA"}]
  },
  "verification": {
    "manufacturable": true,
    "gates_passed": [],
    "gates_failed": [],
    "warnings": []
  },
  "provenance": {
    "created_utc": "",
    "spec_ref": "spec.json",
    "files": {"model.3mf": "sha256:...", "model.step": "sha256:..."}
  }
}
```
`walls` is optional and only present when the caller gave one. `provenance.files` also
carries `model.project.3mf` when that file was produced in the same run.

## Why 3MF over STL
3MF (ISO/IEC 25422:2025) carries units natively, supports multiple objects with per-object
settings, embeds plate layout and thumbnails, and transports as a single container. STL is
unitless and geometry-only. Bambu Studio's flavor adds the 3MF Production Extension plus config
sidecars; a slice against an STL with external preset JSON regularly falls back to defaults.

## Bare 3MF versus project 3MF
`model.3mf` is the contract artifact: a bare, vendor-free 3MF that any slicer can read.
Its weakness is specific to the Bambu Studio GUI. A 3MF that Bambu Studio did not write
itself opens with the notice "The 3mf file has invalid config, load geometry data only":
object names and positions survive, per-object settings and any preset hints do not, and
the part is sliced with whatever presets the app had loaded last. The headless CLI is not
affected; it honours per-object settings in a bare file. Measured with Bambu Studio
02.08.02.61: a part carrying a 4-wall override sliced in the GUI at the stock 2 walls.

`model.project.3mf` (opt-in, `--project`) is the same geometry written by the Bambu Studio
CLI as a genuine project, with the print_intent hints applied as overrides to Bambu's own
machine, process, and filament presets. Two details make it work: the bundled presets are
flattened first, because the CLI does not resolve their `inherits` chains, and
`different_settings_to_system` in `Metadata/project_settings.config` names the overridden
keys, because the CLI leaves it empty and the GUI then trusts its stock preset over the
values in the file. The GUI opens the result with no notice and the overrides visible as
modified settings.

Use the project file when a person will open the handoff in Bambu Studio and press Print.
Use the bare file for everything else: other slicers, headless CLI slicing, archives, and
any transfer where the receiver applies their own presets. A project file embeds Bambu's
preset data and slicing metadata, so it must not be redistributed in repositories or part
libraries that promise bare geometry or vendor-free files; the bare 3MF and the manifest are
what travel. Downstream agents that receive both should still treat print_intent as hints:
the embedded presets are the applied form of the same hints, not a separate authority.

Plate-layout rules that hold for either file: every copy of a part on a plate is its own
`<object>` (Bambu Studio splits `<build><item>`s that share one object into separate
objects on import and applies the name and settings to the first only), and plate positions
live in the item transform with the mesh centred on the origin.

## Bambu Authorization Control System (2025+)
Network print-start requires per-printer developer mode + LAN-only, or routing through Bambu
Connect, or SD-card delivery. Slicing via the CLI is unaffected. This skill therefore stops at
a sliced/sliceable artifact and never assumes a control path.

## AMS
Declare only logical filament roles. Physical slot mapping is RFID-driven at print-send time
and belongs to the downstream printing agent.
