# Explaining results in plain language

Templates for turning each engine result into plain language. Pattern for every item: one
sentence on **what it means and why it matters**, then a **plain offer** of the fix as a simple
choice. Never show coordinates, raw thresholds, JSON, or internal field names. The helper
`scripts/plain_report.py` produces these automatically; use this when you explain by hand or
need to adapt the wording.

## From the manufacturability gate (verification.json)
- **watertight (fail):** "The 3D model isn't fully sealed — there's a gap in its surface that
  print software can't read. I'll close it up."
- **min_wall (fail):** "Part of your design is too thin to print reliably. Thin spots come out
  fragile or don't print at all. I can thicken them — want me to?"
- **min_wall (inconclusive):** "I couldn't fully check the wall thickness on this shape — worth
  a closer look before printing."
- **overhangs (warning):** "Your design has a steep overhang — a section that leans out over
  empty space more than your printer prints cleanly. I can tilt how it's printed, round or
  angle that edge, or add removable scaffolding. Want me to pick the cleanest option?"
- **enclosed_volumes (fail):** "There's a sealed hollow pocket inside with no way out, which
  can trap air or material and fail mid-print. I'll add a small, hidden drain hole."
- **build_volume (fail):** "Your design is bigger than your printer's bed in at least one
  direction. I can shrink it, split it into glue-together pieces, or turn it to fit. What
  works for you?"

## From the structural reviewer (structural_review.json)
- **layer_anisotropy (warning):** "The way it's set to print, the main force on it would pull
  across the layers — the weaker direction. I can reorient it so it's stronger. Worth doing?"
- **stress_risers (warning):** "A few sharp inside corners could crack under stress. I can
  round them slightly so they hold up better."

## From print-failure diagnosis (after a real print)
Translate the failure name into "what you're seeing and why," then the plain fix. Example for
stringing: "Those thin hairy threads between parts are melted plastic oozing as the nozzle
moves. It's usually a printer-setting fix (dialing back how the plastic pulls back), and if
there's a hidden pocket I can add a vent so it has less chance to ooze."

## Always end with the door open
Close with an offer like: "Want the technical details behind any of this? Just ask." Keep the
detailed numbers one question away, never in their face.
