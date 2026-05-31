# FDM Design Loop — Claude Code skills

A pack of [Agent Skills](https://docs.claude.com/en/docs/claude-code/skills) that turn Claude Code
into an iterative **design-for-manufacturing loop for FDM/FFF 3D printing**: describe a part →
generate it as parametric CAD → run deterministic printability gates → review strength →
hand it off to a slicer. Plus a beginner-friendly mode that does all of the above in plain
language.

This repository is both a **plugin** and its own **marketplace**, so it installs by name.

## The skills

| Skill | What it does | Needs Python deps? |
|-------|--------------|:---:|
| `generating-build123d` | Authors/edits parametric parts as build123d (Python/OCCT) code; exports STEP + STL. | ✅ |
| `reviewing-manufacturability-fdm` | Deterministic DFM gates — min wall (ray-cast thickness), overhang angle, enclosed/undrained voids, build-volume fit → `verification.json`. | ✅ |
| `reviewing-structural-loads` | Load direction vs. layer plane, weakest cross-section, stress risers, mass/CoM/inertia → `structural_review.json`. | ✅ |
| `slicing-handoff-bambu` | Packages a verified part into a mm 3MF + archival STEP + manifest; optional Bambu Studio CLI slice. | ✅ |
| `analyzing-print-failures` | Diagnoses a failed print (warping, stringing, layer shift, …) and routes the fix. | — stdlib only |
| `designing-in-plain-language` | Opt-in mode: asks only the questions that matter, in plain words, and explains gate/review results without jargon. Wraps the five above. | — stdlib only |

## Install

```text
/plugin marketplace add Eli-code1/fdm-design-skills
/plugin install fdm-design@fdm-skills
```

The skills are then available in **every project** on that machine. Manage with
`/plugin list`, `/plugin disable fdm-design@fdm-skills`, etc.

> Testing locally before publishing? Point the marketplace at this folder instead:
> `/plugin marketplace add /path/to/fdm-design-skills`

## Python dependencies

Plugins ship *files*, not Python packages. The four geometry skills need
`build123d`, `trimesh`, `scipy`, and `numpy`. Install them into a virtual environment
that your `python` resolves to:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

(`analyzing-print-failures` and `designing-in-plain-language` need nothing installed.)

## How the loop fits together

```
describe a part
      │
      ▼
generating-build123d ──► reviewing-manufacturability-fdm ──► reviewing-structural-loads
      ▲                          │ (fails become concrete code edits)
      └──────────────────────────┘
                                 ▼
                       slicing-handoff-bambu ──► (slicer / printer)

analyzing-print-failures   ← after a real print
designing-in-plain-language ← wraps all of the above for non-experts
```

Each gate failure is handed back to `generating-build123d` as a concrete edit, so the
loop converges on a part that is both modelled and verified-printable.

## License

Not yet licensed (all rights reserved by default). Add a `LICENSE` file before sharing
publicly if you want to permit reuse.
