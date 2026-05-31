# Question bank (plain language)

Ask the fewest of these that matter for the part. Each has a default; "I don't know" is always
fine — use the default and say what you assumed. Map answers to the `PartSpec` field shown.

## 1. What are you making? (no default — this anchors everything)
"Tell me what you want to make and what it needs to do." Free-form. Listen for clues that
answer the questions below so you don't have to ask them.
-> PartSpec.function

## 2. Will it take any force? (default: light / no load)
"Will it need to hold weight or take a pull or push, or is it mostly for looks or for
organizing?" If it bears load, ask roughly which way the force pushes.
-> PartSpec.principal_load  (and informs orientation and material)
Why it matters (only if asked): prints are weaker across their layers, so knowing the force
lets us orient it the strong way.

## 3. Where will it live? (default: indoors -> PLA)
"Indoors at room temperature, or will it be outside, in sunlight, or somewhere hot like a
car or near a stove?" Hot/sunny -> suggest PETG or ASA instead of PLA.
-> PartSpec.material

## 4. Does it need to bend? (default: rigid)
"Does any part of it need to flex or bend, or should it be stiff?" Flex -> TPU.
-> PartSpec.material

## 5. Does it attach to or fit something? (default: standalone)
"Does it clip onto, hold, or fit into another object? If so, what — and do you have its
measurements (or the object handy to measure)?" If yes, capture the sizes.
-> PartSpec.envelope_mm, PartSpec.fits
Plain note to offer: "Printed parts come out a touch off-size, so I'll leave a small gap so it
actually fits — you don't have to worry about that."

## 6. How clean or strong does it need to be? (default: balanced/structural)
"Is this a quick functional part, or does it need to look clean and be sturdy?"
-> PartSpec.profile ("cosmetic" vs "structural")

## Things you might not think to mention (I'll assume good defaults if you don't know)

### Which printer? (default: a common modern printer)
"What 3D printer will you use? The model is best, but the brand is fine — or just say you're
not sure and I'll assume a common one." This sets how big the part can be and how steep an
overhang prints cleanly.
-> PartSpec.printer  (keys printer_profiles.json: bed size, overhang limit)
If they don't know the model: a current Bambu or Prusa class machine is a safe default; say so.

### One material or several? (default: one)
"Most printers use one material at a time. If yours has a multi-material unit (like an AMS)
and you want more than one color or material, tell me — otherwise I'll plan for one."
-> informs filament roles in the handoff; do NOT ask about firmware unless they raise this.

### Nozzle and detail (default: 0.4 mm nozzle, normal layers)
Don't ask unless they bring it up. If they do: "The standard 0.4 mm nozzle most printers ship
with is what I'll assume; it handles the detail in your part fine."
-> PartSpec.nozzle_mm, PartSpec.layer_height_mm

Record every default you applied in PartSpec.assumptions so the person can correct any of them.
