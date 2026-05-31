# Plain-language glossary

Everyday explanations of the terms that come up. Never define a term using other jargon. Use
these inline the first time a term appears, then move on.

- **Overhang** — a part of your model that sticks out over empty space, like a roof with no
  walls under it. Printers build from the bottom up, so a section that leans out too far
  (more than roughly a 45-65 degree lean, depending on the printer) will droop unless the
  printer adds temporary scaffolding.
- **Supports / scaffolding** — temporary structure the printer prints under overhangs to hold
  them up, which you snap off afterward. They work but leave marks, so it's better to design
  so you need fewer.
- **Wall thickness** — how thick the solid shell of your part is. Too thin and it's fragile or
  won't print; we keep it at least a couple of nozzle-widths.
- **Infill** — most printed parts aren't solid inside; they have a honeycomb fill. More fill
  means stronger and heavier; less means faster and lighter.
- **Layer lines** — prints are built from stacked layers, like a loaf of sliced bread. This
  makes a print slightly weaker in the direction that would pull the slices apart, so we tend
  to orient a part so the force on it runs along the slices, not across them.
- **Clearance / tolerance** — printed parts come out a hair bigger or smaller than drawn, so
  when two parts fit together we leave a tiny gap so they actually slide or snap. Handled for
  you.
- **Fillet / chamfer** — rounding an edge (fillet) or cutting it at an angle (chamfer).
  Besides looking nicer, the right one in the right place prints better and is stronger.
- **Brim / raft** — a thin skirt around, or mat under, the first layer to help the print stick
  to the bed. Peeled off after.
- **Warping** — when corners lift off the bed as the plastic cools and shrinks. Big flat parts
  and certain materials are more prone to it.
- **Nozzle** — the tip the melted plastic comes out of. The standard size most printers ship
  with is 0.4 mm; it sets the finest detail you can print.
- **Bed / build volume** — the print surface and the box of space above it. Your part has to
  fit inside it.
- **STL / 3MF** — the file types your printer's software reads. We hand you a 3MF (the modern
  one, which remembers units).
- **STEP** — an editable engineering file you can reopen later in CAD to change the design. We
  hand you one of these too, alongside the printable file.
- **Slicer** — the program that turns your 3D model into the instructions the printer follows.
- **PLA** — the easy, common material; stiff, good for most indoor parts, not for heat.
- **PETG** — a bit tougher and slightly flexible; better for parts that take some stress or a
  little moisture.
- **ABS / ASA** — handle heat and (for ASA) sunlight better, but are fussier to print.
- **TPU** — rubbery and flexible, for parts that need to bend.
