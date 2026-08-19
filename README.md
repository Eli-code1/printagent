# Printagent

Printagent is a pack of [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) for
Claude Code that turns an idea into a verified, printable FDM part. You describe a part, the
skills generate it as parametric CAD, run deterministic printability gates, review its strength,
and package it for a slicer. A beginner-friendly mode runs the whole loop in plain language for
anyone who would rather skip the engineering.

This repository is both a plugin and its own marketplace, so it installs by name.

## The skills

| Skill | What it does | Python deps |
|-------|--------------|:---:|
| `generating-build123d` | Authors and edits parametric parts as build123d (Python/OCCT) code, composing vetted DFM primitives and known-good part templates, then exports STEP and STL. | yes |
| `orienting-for-fdm` | Chooses which way up to print a part to minimize overhangs and support, maximize bed adhesion, and keep a load along the layers; writes the print transform. | yes |
| `reviewing-manufacturability-fdm` | Runs the deterministic DFM gates (minimum wall by cone-SDF thickness, overhang angle, enclosed or undrained voids, and build-volume fit) and writes `verification.json`. | yes |
| `reviewing-structural-loads` | Checks load direction against the layer plane, finds the weakest cross-section, flags stress risers, and reports mass, center of mass, and inertia into `structural_review.json`. | yes |
| `slicing-handoff-bambu` | Packages a verified part into a millimetre 3MF, an archival STEP, and a manifest, with an optional Bambu Studio CLI slice. | yes |
| `publishing-onshape` | Publishes a part to Onshape as a native, visually editable feature tree (real sketches and extrudes) via the REST API. | no, stdlib |
| `verifying-assembly-fit` | Verifies a multi-part kit assembles in real life: measures every joint from the built meshes, applies an as-printed FDM tolerance model, classifies each fit against its intent, and sweeps insertion paths in assembly order. | yes |
| `analyzing-print-failures` | Diagnoses a failed print (warping, stringing, layer shift, and the rest) and routes the fix. | no, stdlib |
| `designing-in-plain-language` | An opt-in mode that asks only the questions that matter, in plain words, and explains the gate and review results without jargon. It wraps the other skills. | no, stdlib |

## Install

```text
/plugin marketplace add Eli-code1/printagent
/plugin install printagent@printagent-skills
```

The skills are then available in every project on that machine. Manage them with `/plugin list`,
`/plugin disable printagent@printagent-skills`, and the rest of the `/plugin` commands.

If you want to test it locally before publishing, point the marketplace at this folder instead:
`/plugin marketplace add /path/to/printagent`.

## Python dependencies

Plugins ship files, not Python packages. The four geometry skills need `build123d`, `trimesh`,
`scipy`, `numpy`, and `rtree` (trimesh's ray casting needs it, but doesn't install it for you).
Install them into a virtual environment that your `python` resolves to:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

The other two skills, `analyzing-print-failures` and `designing-in-plain-language`, need nothing
installed, since they run on the Python standard library alone.

## How the loop fits together

The loop has a clear spine. You describe a part, and `generating-build123d` turns it into
build123d code. `orienting-for-fdm` then chooses which way up to print it, and
`reviewing-manufacturability-fdm` runs the hard gates on that orientation while
`reviewing-structural-loads` checks whether the part survives its load. Every gate failure goes
back to `generating-build123d` as a concrete edit, so the loop keeps tightening until the part is
both modelled and verified-printable. Once it passes, `slicing-handoff-bambu` packages it for the
slicer or the printer.

Two skills sit outside that spine. `analyzing-print-failures` diagnoses a print after it comes off
the bed, and `designing-in-plain-language` wraps the whole loop for anyone who would rather not
learn the engineering to get a working part.

## Parts

Open-source parts published alongside the skills, free to download and print:

| Part | What it is | Size |
|------|------------|------|
| [`air-sampling-cassette`](air-sampling-cassette/) | A flat 3/16 in frame for an air sampling cassette. Watertight STL, prints flat with no supports. | 98.4 × 130.4 × 4.8 mm |

## License

[MIT](LICENSE), copyright 2026 Eli-code1. Use it for anything, including commercial work; just keep
the copyright line.
