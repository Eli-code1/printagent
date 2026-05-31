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

## Why 3MF over STL
3MF (ISO/IEC 25422:2025) carries units natively, supports multiple objects with per-object
settings, embeds plate layout and thumbnails, and transports as a single container. STL is
unitless and geometry-only. Bambu Studio's flavor adds the 3MF Production Extension plus config
sidecars; a slice against an STL with external preset JSON regularly falls back to defaults.

## Bambu Authorization Control System (2025+)
Network print-start requires per-printer developer mode + LAN-only, or routing through Bambu
Connect, or SD-card delivery. Slicing via the CLI is unaffected. This skill therefore stops at
a sliced/sliceable artifact and never assumes a control path.

## AMS
Declare only logical filament roles. Physical slot mapping is RFID-driven at print-send time
and belongs to the downstream printing agent.
