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
| `verifying-assembly-fit` | Verifies a multi-part kit assembles in real life: measures every joint from the built meshes, applies an as-printed FDM tolerance model, classifies each fit against its intent, and sweeps insertion paths in assembly order. | yes |
| `slicing-handoff-bambu` | Packages a verified part into a millimetre 3MF, an archival STEP, and a manifest, with an optional Bambu Studio CLI slice. | yes |
| `publishing-onshape` | Publishes a part to Onshape as a native, visually editable feature tree (real sketches and extrudes) via the REST API. | no, stdlib |
| `analyzing-print-failures` | Diagnoses a failed print (warping, stringing, layer shift, and the rest) and routes the fix. | no, stdlib |
| `designing-in-plain-language` | An opt-in mode that asks only the questions that matter, in plain words, and explains the gate and review results without jargon. It wraps the other skills. | no, stdlib |

## Install

You need [Claude Code](https://docs.claude.com/en/docs/claude-code/overview). From a Claude Code
session:

```text
/plugin marketplace add Eli-code1/printagent
/plugin install printagent@printagent-skills
```

The same thing from a terminal:

```bash
claude plugin marketplace add Eli-code1/printagent
claude plugin install printagent@printagent-skills
```

The skills are then available in every project on that machine. `claude plugin list`,
`claude plugin disable printagent@printagent-skills`, and
`claude plugin update printagent@printagent-skills` manage them from there, as does the
interactive `/plugin` menu. The `plugin@marketplace` form matters: `claude plugin update`
rejects the bare name.

To try a local checkout first, point the marketplace at the folder instead:
`claude plugin marketplace add /path/to/printagent`.

## Python dependencies

Plugins ship files, not Python packages. Six of the nine skills run real geometry and need a
Python environment: `generating-build123d`, `orienting-for-fdm`,
`reviewing-manufacturability-fdm`, `reviewing-structural-loads`, `verifying-assembly-fit`, and
`slicing-handoff-bambu`.

**You do not need to clone this repository.** Installing the plugin already fetched every script;
these two lines add the Python side, straight from the URL:

```bash
python3 -m venv ~/printagent-env && source ~/printagent-env/bin/activate
pip install -r https://raw.githubusercontent.com/Eli-code1/printagent/main/requirements.txt
```

Check it landed:

```bash
python -c "import build123d, trimesh, scipy, rtree, shapely; print('printagent deps ok')"
```

Start Claude Code from that activated environment so the skills resolve the packages. If you did
clone the repo, `pip install -r requirements.txt` from the checkout does the same thing.

That set is `build123d` (which pulls in cadquery-ocp, the OCCT kernel), `trimesh`, `numpy`, and
`scipy`, plus four packages trimesh calls optional extras but imports at call time, so they are
hard requirements here: `rtree` for the ray casting behind the min-wall and fit probes,
`networkx` and `lxml` for the 3MF writer, and `shapely` for cross-sections. `requirements.txt`
also pins `bd_warehouse` for thread and fastener generators; no skill in this repo imports it
today, so drop that line if you do not model printed threads. Verified on macOS with Python 3.11.

The other three skills, `publishing-onshape`, `analyzing-print-failures`, and
`designing-in-plain-language`, need nothing installed, since they run on the Python standard
library alone.

## Optional external tools

Two skills reach outside Python, and both stay useful without their tool:

- `slicing-handoff-bambu` writes the 3MF, the STEP, and the manifest with no external tool.
  Only the optional `--slice` step needs a local Bambu Studio, and it finds the binary itself:
  `PATH` first, then the standard macOS and Linux install locations. On a normal install you
  name nothing. For an unusual one, pass `--bambu-bin`, or set the `bambu_bin` option once with
  `/plugin configure printagent`. Slicing is in scope, starting a print is deliberately not.
- `publishing-onshape` needs an Onshape account and API keys from the
  [developer portal](https://cad.onshape.com/appstore/dev-portal). Just ask Claude to set up
  Onshape and the skill walks you through it, using
  `scripts/setup_credentials.py`: `--check` reports whether keys exist, `--instructions` prints
  the steps, `--write` prompts for the keys in your own terminal and saves
  `~/.config/onshape/credentials` with 0600 permissions, and `--verify` confirms them against
  the live API. Type the secret into your terminal, never into the chat. Keys never enter the
  repo and are never logged.

## Printers

The gates derive their thresholds from nozzle diameter, layer height, and a cosmetic or
structural profile, against a named printer profile: `generic` (the default), `bambu_x1c`,
`bambu_p1s`, `bambu_a1`, `bambu_h2d`, `prusa_mk4s`, and `prusa_core_one`. Each profile carries
its nozzle, build volume, usable bed margin, and safe overhang angle, in
`skills/reviewing-manufacturability-fdm/scripts/printer_profiles.json`. Adding a printer means
adding an entry there; nothing else is printer-specific.

## How the loop fits together

The loop has a clear spine. You describe a part, and `generating-build123d` turns it into
build123d code. `orienting-for-fdm` then chooses which way up to print it, and
`reviewing-manufacturability-fdm` runs the hard gates on that orientation while
`reviewing-structural-loads` checks whether the part survives its load. Every gate failure goes
back to `generating-build123d` as a concrete edit, so the loop keeps tightening until the part is
both modelled and verified-printable. For a kit of mating parts, `verifying-assembly-fit` then
proves the parts actually go together before any of them ship. Once that passes,
`slicing-handoff-bambu` packages the result for the slicer or the printer.

Three skills sit outside that spine. `publishing-onshape` pushes a finished part to Onshape as an
editable feature tree, for when you want to carry on in GUI CAD. `analyzing-print-failures`
diagnoses a print after it comes off the bed, and `designing-in-plain-language` wraps the whole
loop for anyone who would rather not learn the engineering to get a working part.

## Status

Version 0.1.0, developed and used on macOS. Issues and pull requests are welcome at
[Eli-code1/printagent](https://github.com/Eli-code1/printagent). Printagent is an independent
project and is not affiliated with or endorsed by Bambu Lab, Onshape, or Anthropic.

## License

[MIT](LICENSE), copyright 2026 Eli-code1. Use it for anything, including commercial work; just keep
the copyright line.
