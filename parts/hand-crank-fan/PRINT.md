# How to print, assemble, and use the hand-crank fan

This is the **snap-together** version: **5 parts on one plate** — a base, a hand-wheel, a
fan-pinion, and **two press-in pins**. No floating islands, so no "floating regions" warning.

Print **`handoff/model.3mf`** (all 5 parts are already laid out on the plate).

## Slice settings

Open `handoff/model.3mf` in Bambu Studio, pick **X1C** and **PLA**:

| Setting | Value | Why |
|---------|-------|-----|
| Supports | **OFF** | The gears lie flat, the blades self-support, the base bridges its own pockets. Supports just clutter the teeth. |
| Brim | ON (5 mm) | Helps the base and the two little pins stick. |
| Layer height | 0.2 mm | |
| Infill | 10-15% | The base is a hollow ribbed shell; sparse infill keeps it light. |

If the fan blades look like they sag in the preview, you can enable supports **for the fan part
only** — it won't hurt anything now that the parts are separate.

## Assemble it (about 10 seconds)

1. Set the **wheel** flat on the base, bore over the **left** hole.
2. Push a **pin** straight down through the wheel's center hole into the base hole until the head
   seats on the wheel. The pin's lower section **press-fits into the base** (it stays put); the
   wheel spins freely on the shaft, held down by the head.
3. Do the same with the **fan-pinion** on the **right** hole.
4. Spin the knob — the fan should whirl at about **4×** your hand speed.

## Fit tuning (printers vary)

- **Pin too loose in the base** (falls out): scale the base holes down ~0.1 mm, or put a small
  drop of glue **in the base hole** (never on the spinning shaft).
- **Pin too tight to push in**: scale the holes up ~0.1 mm, or ease the hole with a 5 mm drill.
- **Gear stiff to spin**: give it a few firm turns to wear in; or sand the gear's bottom face
  lightly. There's a deliberate ~0.36 mm of gear backlash, so you'll feel a little free play
  before the wheel "catches" the fan — that's normal.

## Verified before printing

- **Spins & drives:** `check_spin.py` — bore/shaft spin clearance 0.40 mm, press interference
  0.10 mm, head retention 0.55 mm; gears mesh at +0.36 mm with no jam over a full tooth cycle;
  blades clear the wheel.
- **Walls:** every part's true minimum wall is >= ~1 mm (base ribs 2-2.4 mm, teeth/blades ~2 mm,
  pins 5.1 mm). The `min_wall` gate "fail" is only grazing rays on sharp tooth tips / rib
  corners — see `verification.json`.
- **Fits the X1C bed** (199 x 189 mm plate), no enclosed voids.

## Files

- `fan.py` — parametric model. Tune fits (`BASE_HOLE_R`, `GEAR_BORE_R`), gears, size, lean here.
- `fan.step` / `fan.stl` — the 5-part plate geometry.
- `verification.json`, `check_per_body.py`, `check_spin.py`, `verify_assembly.py` — the checks.
- `render.py` (assembled views) / `render_plate.py` (plate) / `renders/`.
- `handoff/` — the package to hand to a printing agent.
