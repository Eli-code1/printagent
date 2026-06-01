# build123d idioms (concentrated reference)

Assumes build123d >= 0.10, algebra mode unless noted. APIs are version-sensitive, pin it.

## Two modes
**Algebra (preferred for generated code)**, objects combine with operators, placement by
multiplying a Location:

    from build123d import *
    part = Box(40, 20, 10)
    part -= Pos(10, 0, 5) * Cylinder(radius=2.5, height=10)   # cut a hole
    part += Pos(-15, 0, 10) * Box(6, 6, 4)                    # add a boss
    part &= Sphere(25)                                        # intersect

**Builder**, context managers, for when a feature needs the running context:

    with BuildPart() as bp:
        Box(40, 20, 10)
        with Locations((10, 0, 0)):
            Hole(radius=2.5)
    part = bp.part

Do not mix the two in one part.

## Primitives
3D: `Box`, `Cylinder`, `Sphere`, `Cone`, `Torus`, `Wedge`.
2D: `Rectangle`, `Circle`, `Ellipse`, `RegularPolygon`, `Polygon`, `SlotOverall`, `Text`.
2D → 3D: `extrude(sketch, amount)`, `revolve(sketch, axis)`, `loft([s1, s2])`,
`sweep(sketch, path)`.

Constructors take `align=(Align.MIN|CENTER|MAX, ...)`. To sit a body on z=0:
`Cylinder(3, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))`.

## Placement
`Pos(x, y, z)`, `Rot(rx, ry, rz)`, `Plane.XY/XZ/YZ` (and `Plane(origin=, z_dir=)`),
`Axis.X/Y/Z`, `Location`. Compose by multiplying: `Rot(0, 90, 0) * Pos(0, 0, 5) * Cylinder(2, 8)`.

## Selectors (return ShapeList, index and slice freely)
    part.faces()              part.edges()              part.vertices()
    .filter_by(GeomType.CIRCLE)        # planar/cylindrical/etc.
    .filter_by(Axis.Z)                 # faces whose normal ~ Z; edges ~ Z
    .filter_by(Plane.XY)
    .sort_by(SortBy.AREA | SortBy.RADIUS | SortBy.LENGTH | SortBy.DISTANCE)
    .sort_by(Axis.Z)                   # by position along axis
    .group_by(Axis.Z)                  # list of ShapeLists by level
Examples:
    top = part.faces().sort_by(Axis.Z)[-1]
    big_hole = part.edges().filter_by(GeomType.CIRCLE).sort_by(SortBy.RADIUS)[-1]
    bottom_edges = part.faces().sort_by(Axis.Z)[0].edges()

## Modifying ops
    part = fillet(part.edges().filter_by(Axis.Z), radius=1.5)    # functional; returns new solid
    part = chamfer(bottom_edges, length=0.5)
    part = offset(part, amount=-2.0, openings=top)               # shell to 2 mm wall, open top
    part = mirror(part, about=Plane.XZ)

## Test as you go
After each major step, assert the invariant you expect, `assert part.is_valid()`,
`assert abs(part.volume - expected) < tol`, `len(part.faces().filter_by(GeomType.CIRCLE)) == n`.
Cheap inline checks catch a bad selector before it propagates.
