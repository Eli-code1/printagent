# Air sampling cassette

An open-source part released with [Printagent](../README.md). The STL is production
geometry, published here so anyone can download and print it.

![Top, front, and isometric views of the cassette](preview.png)

## Download

**[`air-sampling-cassette.stl`](air-sampling-cassette.stl)** — 137 KB binary STL, 2,740 triangles.

Revision `2026-07-01` (original filename `7-1-26 Prod Cassette.stl`).

## Measured geometry

Every number below was measured off the mesh itself with `trimesh`, not copied from a drawing.

| Property | Value |
|---|---|
| Bounding box | 98.425 × 130.420 × 4.763 mm  (3.8750 × 5.1347 × 0.1875 in) |
| Wall thickness (nominal) | 4.763 mm = **3/16 in** exactly |
| Solid volume | 10 674.8 mm³ (10.675 cm³) |
| Surface area | 11 000.3 mm² |
| Solid mass estimate | ≈13.2 g PLA, ≈13.6 g PETG (100 % infill) |
| Topology | watertight, consistent winding, 1 body, genus 4 |
| Degenerate faces | 0 |

The part is a flat, constant-thickness frame: a U-shaped band closed by a rectangular tab at
one end. Feature steps land on Z = 0, 1.588, 2.223, 2.858, 3.493, 4.763 mm — i.e. 0, 1/16,
0.0875, 0.1125, 0.1375, 3/16 in. The model was authored in inches; the STL, per the format's
convention, carries no units, so **import it as millimetres**. A slicer that assumes inches
will scale it 25.4× too large.

## Printing it

The geometry is flat and thin, so it lies straight on the bed in its native orientation with the
98.4 × 130.4 mm face down — no rotation needed, and it fits any common 180 mm or larger bed.
Print it solid or near-solid: at 4.76 mm tall the whole part is essentially wall and the infill
saving is negligible.

These are geometric observations, not a verified process. The Printagent gates
(`reviewing-manufacturability-fdm`, `orienting-for-fdm`) have **not** been run against this
mesh; run them yourself if you want thickness, overhang, and drainage checked against your
printer and material.

## License

MIT, the same as the rest of this repository — see [LICENSE](../LICENSE). Use it for anything,
including commercial work; just keep the copyright line.
