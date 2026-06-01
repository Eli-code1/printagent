# Question bank (plain language)

Two ways in: the **template router** (try first) and the **five core questions** (fallback).
Either way, ask the **fewest** questions that matter, easy ones first, offer a default for each,
and accept "I don't know" by using the default and saying what you assumed. Map answers to the
`PartSpec` field shown.

## Template-first router (try this before the five questions)
If the request clearly matches a common part family, propose that known-good design and ask only
for the few numbers it needs. Do NOT run the full five questions when a family matches with
confidence; the family already answers most of them. Fall back to the five core questions only
when nothing matches.

| Family | Trigger words | Ask only for | Baked-in answers |
| --- | --- | --- | --- |
| Holder / cradle | holder, cradle, dock, stand for a phone or remote | the held object's width, depth, and thickness | standalone, light load, palm-to-hand size, indoor |
| Bracket | bracket, shelf bracket, L-bracket, support | the two mating face sizes, and the load it carries | load-bearing, attaches to a wall or panel |
| Hook | hook, peg, hanger | the rail or rod diameter it hangs on, and the load | load-bearing, attaches to a rail |
| Box with lid | box, case, enclosure, container with a lid | inside width, depth, and height | standalone, light load, indoor |
| Adapter | adapter, coupler, reducer, converter | the two diameters or profiles it joins | light load, fits two named objects |
| Mounting plate | mounting plate, base plate, VESA plate | the hole pattern (spacing and bolt size) and outline | attaches via bolts, load-bearing |
| Tray | tray, organizer, drawer insert, divider | outside width and depth, and divider count | standalone, light load, indoor |
| Stand | stand, easel, riser, display stand | what it holds and the viewing angle | standalone, light-to-medium load, indoor |
| Plaque | plaque, sign, nameplate, label | the text and the outline size | standalone, decorative, indoor |

When a family matches: name it back in plain words ("sounds like a wall bracket"), state the
baked-in answers as assumptions they can change, and ask only for the numbers in the "Ask only
for" column. Record the family in PartSpec.assumptions.

## The five core questions (fallback when no family matches)
HARD CAP: ask **at most five** questions before any design work, easy ones first, then **one**
confirmation summary. NEVER ask a sixth question unless the user explicitly invites more. If you
feel a sixth would help, fold it into the confirmation summary as a stated assumption instead.
Everything not in this list (material, layer height, nozzle, infill, walls, supports, and
orientation) MUST be auto-defaulted, never asked; note "you can change this" once at confirmation.

### Q1. What is the thing? (no default; this anchors everything)
"Tell me what you want to make and what it needs to do." Free-form. Listen for clues that answer
Q2 through Q5 so you can skip them.
-> PartSpec.function

### Q2. What does it attach to, hold, or fit? (default: standalone)
"Does it clip onto, hold, or fit another object? If it fits something, what are that object's
measurements (or do you have the object handy to measure)?" If it fits something, capture the
sizes; without them you cannot size the part.
-> PartSpec.fits, PartSpec.envelope_mm
Plain note to offer: "Printed parts come out a touch off-size, so I will leave a small gap so it
actually fits; you do not have to worry about that."

### Q3. Roughly how big? (default: hand size)
Offer size bands so they do not need numbers: "About palm size (fits in one hand), hand size
(fills your hand), or two-hand size (needs both hands)?" Convert the band to a rough envelope.
-> PartSpec.envelope_mm

### Q4. Load-bearing or decorative? (default: light / no load)
"Will it hold weight or take a pull or push, or is it mostly for looks or for organizing?" If it
bears load, ask roughly which way the force pushes (this is part of the same question, not a
sixth).
-> PartSpec.principal_load, PartSpec.profile
Why it matters (only if asked): prints are weaker across their layers, so knowing the force lets
us orient the part the strong way.

### Q5. Where will it live? (default: indoors -> PLA)
Offer the places, not the materials: "Indoors at room temperature, in a hot car, outdoors,
in a kitchen, or in a bathroom?" Map the place to the material yourself.
-> PartSpec.material

### Confirmation summary (always, before design work)
Read back, in plain language, the thing, what it attaches to or fits, the rough size, the load,
and where it lives. List the auto-defaults you applied (material, layer height, nozzle, infill,
walls, supports, and orientation) in one compact line, and add exactly one note:
"You can change any of this; just say the word." Then proceed. Record every default in
PartSpec.assumptions so the person can correct any of them.

## Auto-defaulted, never asked (decide these silently)
These are set by the engines and your defaults; surface them only in the confirmation line, and
only discuss one if the user raises it.

### Printer (default: a common modern printer)
Infer or assume; do not spend one of the five on it. If the user names a printer, use it. The
model sets how big the part can be and how steep an overhang prints cleanly. A current Bambu or
Prusa class machine is a safe default; say so in the confirmation line.
-> PartSpec.printer  (keys printer_profiles.json: bed size, overhang limit)

### Material (default: PLA indoors; mapped from Q5)
Indoor -> PLA. Hot car or near a stove -> PETG or ASA. Outdoors in sun -> PETG or ASA. Needs to
flex -> TPU. Decide from Q5; do not ask separately.
-> PartSpec.material

### One material or several (default: one)
Assume one. Plan for more only if the user mentions a multi-material unit (like an AMS) or
several colors. Do NOT ask about firmware unless they raise multi-material.

### Nozzle, layers, infill, walls, supports, orientation (default: standard)
Auto-defaulted: 0.4 mm nozzle, normal layers, standard infill and walls, supports only where the
geometry needs them, and orientation chosen for strength or print quality. Never ask; mention
only if the user brings one up.
-> PartSpec.nozzle_mm, PartSpec.layer_height_mm

## Volunteered side-questions (raise only when the context triggers one)
A novice would not know to raise these. Surface each one only when its trigger appears, in plain
language, as a short heads-up, not a question that counts against the five.

- **Holes print undersize.** Trigger: the user wants a bolt, screw, or rod to fit a hole (for
  example "an M3 bolt should go through"). Say: "FDM holes come out a little tight, so I will
  make an M3 hole about 3.3 mm so the bolt actually fits."
- **Heat.** Trigger: hot car, near a stove, dishwasher, or anything warm. Say: "PLA starts to
  soften above about 55 C, so for heat I will use PETG or ASA instead."
- **UV and outdoors.** Trigger: outside, in sunlight, on a deck or in a yard. Say: "PLA gets
  brittle in sunlight over time, so for outdoors I will use a UV-tougher material like ASA."
- **Food contact.** Trigger: food, drink, kitchen utensil, or cup. Say: "Printed layer lines
  trap bacteria, so this is not food safe as printed; it would need a food-safe coating, or
  treat it as for dry or short contact only."
- **Bed adhesion (first layer).** Trigger: a wide flat base, a tall thin part, or first-time
  printing. Say: "The very first layer has to stick to the bed or the print lifts; a clean,
  level bed and a brim help, and I have kept the base flat to make that easier."
