# FDM design-for-manufacturing rules

Quantitative DFM defaults for FDM/FFF. All numbers assume a **0.4 mm nozzle / 0.2 mm layer
height** unless a scaling formula is given; `line_width ≈ nozzle`. `fdm_rules.py` is the
machine-readable source of truth for the numbers the scripts enforce. Rows marked **[gate]**
are enforced by a script in this skill today; rows marked *[advisory]* are for the generating
and structural skills to reason with.

| Rule | Default (0.4/0.2) | Scaling | Status |
|---|---|---|---|
| Min wall, cosmetic | 0.8 mm | `2 × line_width` | **[gate]** |
| Min wall, structural | 1.2–1.6 mm | `4 × line_width` | **[gate]** |
| Min wall in Z | 0.8 mm | `4 × layer_height` | *[advisory]* |
| Max overhang (from vertical), classic | 45° | hard | **[gate]** |
| Max overhang, modern part-cooled (X1C/MK4S/Core One) | 60–75° | profile | **[gate]** |
| Max unsupported bridge | ≤10 mm (PLA), ≤5 mm (PETG/ABS), ≤3 mm (TPU) | material | *[advisory]* |
| Enclosed cavity vent | ≥3 mm hole on every sealed void | — | **[gate]** |
| Build-volume fit | footprint+height ≤ bed − margin, Z up | profile | **[gate]** |
| Min embossed text, top | 0.5 mm stroke × 0.5 mm relief, ≥4 mm font | stroke ≥ line_width | *[advisory]* |
| Min embossed text, side wall | 0.8 mm stroke × ≥2 mm relief, 10 pt bold | larger | *[advisory]* |
| Min pin/boss diameter | ≥1.8 mm (prefer ≥2 mm) | `4 × line_width` | *[advisory]* |
| Hole XY compensation | +0.2 mm on diameter (range +0.1–0.4) | measured ~0.23 mm @ X1C | *[advisory]* |
| Clearance fit (sliding) | 0.3–0.5 mm/side | `≥ 1 layer_h` | *[advisory]* |
| Press fit | −0.05 to −0.1 mm, chamfer lead-in | material | *[advisory]* |
| Print-in-place gap | 0.2–0.4 mm (typ. 0.3) | `≥ 1 layer_h` | *[advisory]* |
| Elephant's-foot chamfer | 0.5 mm × 45° on bottom edges | `2–4 × first_layer_h` | *[advisory]* |
| Layer-line anisotropy | Z strength = 40–70% of XY | orient tensile load in XY | *[advisory]* |
| Chamfer vs fillet | chamfer downward edges, fillet upward; no downward fillets | — | *[advisory]* |
| Horizontal hole shape | teardrop (Ø≤4 mm) or flat-roof+0.4 mm (Ø≥8 mm) | — | *[advisory]* |
| Min hole | ≥1 mm vertical, ≥2 mm horizontal | nozzle | *[advisory]* |
| Printed threads | none below M6; +0.2–0.4 mm clearance on M6+ internal | heat-set for M2–M5 | *[advisory]* |
| Heat-set insert pilot | M3 → Ø4.0–4.2, M4 → Ø5.6–6.0, M5 → Ø6.4 | `OD − 0.1 (PLA/PETG)` | *[advisory]* |
| Mouse-ears | Ø8–12 mm × 1–2 layers at sharp corners | shrink-prone, parts > 50 mm | *[advisory]* |
| Layer-height ceiling | ≤ 75% of nozzle diameter | hard | *[advisory]* |

Sources: Prusa Knowledge Base, Bambu Lab Wiki, Protolabs Network/Hubs, Markforged, Slant3D,
Stratasys Direct, Hydra Research, Core77 design rules, Marston Makerspace fits study, Rahix
"Design for 3D-Printing". The 45°→75° overhang creep tracks part-cooling improvements on
modern machines and is read per-printer from `printer_profiles.json`.
