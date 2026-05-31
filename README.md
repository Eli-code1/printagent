# FDM Design Loop, Claude Code skills

A pack of [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) that turns Claude
Code into an iterative design-for-manufacturing loop for FDM and FFF 3D printing. You describe a
part, the loop generates it as parametric CAD, runs deterministic printability gates, reviews its
strength, and packages it for a slicer. A beginner-friendly mode runs all of that in plain
language.

This repository is both a plugin and its own marketplace, so it installs by name.

## The skills

| Skill | What it does | Python deps |
|-------|--------------|:---:|
| `generating-build123d` | Authors and edits parametric parts as build123d (Python/OCCT) code, then exports STEP and STL. | yes |
| `reviewing-manufacturability-fdm` | Runs the deterministic DFM gates (minimum wall by ray-cast thickness, overhang angle, enclosed or undrained voids, and build-volume fit) and writes `verification.json`. | yes |
| `reviewing-structural-loads` | Checks load direction against the layer plane, finds the weakest cross-section, flags stress risers, and reports mass, center of mass, and inertia into `structural_review.json`. | yes |
| `slicing-handoff-bambu` | Packages a verified part into a millimetre 3MF, an archival STEP, and a manifest, with an optional Bambu Studio CLI slice. | yes |
| `analyzing-print-failures` | Diagnoses a failed print (warping, stringing, layer shift, and the rest) and routes the fix. | no, stdlib |
| `designing-in-plain-language` | An opt-in mode that asks only the questions that matter, in plain words, and explains the gate and review results without jargon. It wraps the five skills above. | no, stdlib |

## Install

```text
/plugin marketplace add Eli-code1/fdm-design-skills
/plugin install fdm-design@fdm-skills
```

The skills are then available in every project on that machine. Manage them with `/plugin list`,
`/plugin disable fdm-design@fdm-skills`, and the rest of the `/plugin` commands.

If you want to test it locally before publishing, point the marketplace at this folder instead:
`/plugin marketplace add /path/to/fdm-design-skills`.

## Python dependencies

Plugins ship files, not Python packages. The four geometry skills need `build123d`, `trimesh`,
`scipy`, and `numpy`. Install them into a virtual environment that your `python` resolves to:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

The other two skills, `analyzing-print-failures` and `designing-in-plain-language`, need nothing
installed, since they run on the Python standard library alone.

## How the loop fits together

The loop has a clear spine. You describe a part, and `generating-build123d` turns it into
build123d code. `reviewing-manufacturability-fdm` then runs the hard gates, and
`reviewing-structural-loads` checks whether the part survives its load. Every gate failure goes
back to `generating-build123d` as a concrete edit, so the loop keeps tightening until the part is
both modelled and verified-printable. Once it passes, `slicing-handoff-bambu` packages it for the
slicer or the printer.

Two skills sit outside that spine. `analyzing-print-failures` diagnoses a print after it comes off
the bed, and `designing-in-plain-language` wraps the whole loop for anyone who would rather not
learn the engineering to get a working part.

## License

[MIT](LICENSE), copyright 2026 Eli-code1. Use it for anything, including commercial work; just keep
the copyright line.
