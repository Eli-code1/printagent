# OCCT kernel failure playbook

build123d/CadQuery share the OCCT kernel and its failure modes. Symptom → cause → workaround:

| Symptom | Likely cause | Workaround |
|---|---|---|
| `fillet`/`chamfer` raises or returns invalid | radius/length ≥ an adjacent feature or edge length | reduce the value; apply fillets/chamfers **last**; fillet fewer edges per call; split into stages |
| Boolean returns empty or invalid solid | coincident/overlapping faces (e.g. cut exactly flush) | extend the cutter past the surface by a small epsilon (0.01–0.1 mm); avoid faces that land exactly coplanar |
| `loft` self-intersects or fails | profiles mis-aligned, non-tangent, or twisted | align profile start points; reduce twist; add an intermediate profile; or substitute `sweep`/`extrude` |
| `sweep` fails on a tight path | path curvature smaller than the section | enlarge the path radius, shrink the section, or loft instead |
| `offset`/shell collapses | inward amount ≥ local half-thickness, or sharp internal corners | reduce the shell thickness; pre-round internal corners; shell before adding small features |
| STEP import has no solid | imported as shell/compound | `import_step(...).solids()` or sew faces; verify `.is_valid()` |

General: wrap kernel-fragile calls in try/except and retry with a reduced parameter before
giving up; prefer building robust base geometry first and decorating (fillets, small bosses,
text) last.
