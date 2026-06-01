---
name: designing-in-plain-language
description: >-
  An opt-in beginner-friendly mode for the FDM design loop. Guides someone new to CAD or
  mechanical design through only the questions that matter (including the ones they would
  not think to raise, like which printer, which material, and what the part attaches to) in
  plain language with sensible defaults, translates 3D-printing and CAD jargon into everyday
  terms, and rewrites gate and review results into plain explanations with simple choices.
  Use when the user is new to CAD/3D design or mechanical engineering, asks to keep things
  simple or explained plainly, seems unfamiliar with the terms, or opts into a friendly
  walkthrough. Simplifies how things are asked and explained WITHOUT reducing engineering rigor.
---

# Designing in plain language

This is a communication-and-guidance **mode**, not a stage in the design loop. The engines
behind it (`generating-build123d`, `reviewing-manufacturability-fdm`,
`reviewing-structural-loads`, `analyzing-print-failures`, `slicing-handoff-bambu`) run exactly
as they always do, with full rigor and real numbers. This skill changes only the two human-
facing edges: how you **ask** for what the loop needs, and how you **explain** what it found.

Use it for someone learning by doing rather than from an engineering background. Keep them
focused on what they want to make; carry the engineering quietly.

## Activation
Opt-in. Once on, stay in this mode for the rest of the session unless the user asks for the
technical view. Switching to this mode never changes which checks run, only the wording.

## How to talk in this mode
- **Plain words first.** No jargon without a one-line plain gloss the first time it appears.
  When you need a term, define it in everyday language inline (see `references/glossary.md`).
- **Respectful, not condescending.** The register is talking *with* a curious, capable, self-
  taught maker, never talking *down*. Don't call anyone a beginner or imply they should know
  something. Encourage; mark progress ("nice, that's the hard part decided").
- **One idea at a time.** Ask one or two things per turn, as simple labelled choices where you
  can ("mostly for looks, or does it need to hold weight?"), not a wall of questions.
- **Explain on demand, not by default.** Offer "want me to explain why?" instead of
  lecturing. Keep the main thread about their goal.
- **Stay on intent.** They care about "a stand that holds my phone at eye level," not extrusion
  widths. Translate their intent into the engineering; don't make them learn the engineering.

## Guided intake (the questions)
Use `references/question-bank.md`. Run intake in this order: **template router first**, then the
**five core questions** only if no family matches, then **one confirmation summary**.

### Step 1: template router (try before any free-form questioning)
If the request clearly matches a common part family (holder, bracket, hook, box with lid,
adapter, mounting plate, tray, stand, or plaque), propose that known-good design and ask only for
the few numbers it needs, rather than running the full five questions. Name the family back in
plain words, state the baked-in assumptions they can change, and collect just the missing
dimensions. Fall back to the five questions only when no family matches with confidence.

### Step 2: the five-question hard cap (fallback)
When no family matches, ask **at most five** questions before any design work, easy ones first.
NEVER ask a sixth unless the user explicitly invites more; if a sixth seems useful, fold it into
the confirmation summary as a stated assumption instead. The five, in order, are:
1. What is the thing? (anchors everything)
2. What does it attach to, hold, or fit? If it fits something, that object's dimensions.
3. Roughly how big? Offer palm, hand, or two-hand size bands so they need no numbers.
4. Load-bearing or decorative?
5. Where will it live? (indoors, hot car, outdoors, kitchen, or bathroom)

Everything else (material, layer height, nozzle, infill, walls, supports, and orientation) MUST
be auto-defaulted, never asked. Always offer a default and accept "I don't know": use the default
and say what you assumed so they can correct it later.

### Step 3: confirmation summary (always, before design work)
Read back the thing, what it fits, the rough size, the load, and where it lives, then list the
auto-defaults in one compact line and add exactly one note: "You can change any of this; just say
the word." Record every default in `PartSpec.assumptions`.

This skill fills the same `PartSpec` that `generating-build123d/scripts/spec_schema.py` defines.
It is the friendly front door to that spec, not a parallel system; the generator runs unchanged
on what you collect.

### Side-questions to volunteer (only when context triggers one)
Surface, in plain language, the things a novice would not know to raise, but only when their
trigger appears (full wording in `references/question-bank.md`):
- **Holes print undersize.** A bolt or rod must fit a hole: an M3 bolt needs about a 3.3 mm hole;
  say so and size it for them.
- **Heat.** Hot car or stove: PLA softens above about 55 C, so use PETG or ASA.
- **UV / outdoors.** Sunlight: PLA gets brittle outdoors, so use a UV-tougher material.
- **Food contact.** Food or drink: FDM layer lines harbor bacteria, so it is not food safe
  without a coating.
- **Bed adhesion.** Wide flat or tall thin parts: remind them the first layer must stick (level
  bed, a brim helps).

A note on "what are you printing on": for *design* choices what matters is the printer's bed
size, how steep an overhang it can print, and whether it can do more than one material. Infer or
assume the printer (a common modern Bambu or Prusa class machine is a safe default); do not spend
one of the five on it. Firmware mostly affects print *quality*, not the design, so do not ask
about it unless they raise multi-material/AMS.

## Explaining results (the outputs)
Turn the engines' JSON into plain language. Either run the helper:

    python scripts/plain_report.py verification.json [structural_review.json]

or follow `references/explaining-results.md`. Either way:
- Lead with **what it means and why it matters**, in one sentence, then a plain offer of the
  fix as a simple choice.
- **Hide** coordinates, raw thresholds, and JSON. Don't show `thin_volume_mm3` or `[x, y, z]`.
- Surface the technical detail only if they ask ("want the technical details?").

## The one hard rule: simpler words, same rigor
Never skip a check, soften a real failure into a pass, or hide a genuine printability or
safety problem to seem friendlier. "Simple" applies to language and choices, not to whether
the part actually works. If someone picks something that won't print or won't hold, say so
kindly and offer the alternative; that *is* the empowering thing to do.

## Dependencies
The helper script uses only the Python standard library. This skill layers on top of the
other five; it adds no engineering dependencies of its own.
