// Apollo sled — Onshape-native parametric twin of sled.py.
//
// Use: in a Feature Studio, select all and paste this file over the contents.
// If the two version numbers below get underlined, click the Feature Studio's
// "Update to latest version" control (or retype the numbers the empty studio
// had) — only the numbers matter, nothing else changes.
//
// Parity note: this twin carries the plate, kite ribs (coupon v6 fit numbers as
// defaults), notch, boss, tap-ready 1/4-20 bore, and both chamfers. The modeled
// printed thread stays in sled.py, which remains the source of truth for
// printing; this feature is for visual design iteration in Onshape.

FeatureScript 1746;
import(path : "onshape/std/common.fs", version : "1746.0");

annotation { "Feature Type Name" : "Apollo sled" }
export const apolloSled = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Plate width" }
        isLength(definition.plateW, { (millimeter) : [40, 56, 120] } as LengthBoundSpec);

        annotation { "Name" : "Plate depth" }
        isLength(definition.plateD, { (millimeter) : [30, 44, 100] } as LengthBoundSpec);

        annotation { "Name" : "Plate thickness" }
        isLength(definition.plateT, { (millimeter) : [2, 3, 8] } as LengthBoundSpec);

        annotation { "Name" : "Front notch width" }
        isLength(definition.notchW, { (millimeter) : [3, 8, 20] } as LengthBoundSpec);

        annotation { "Name" : "Front notch depth" }
        isLength(definition.notchD, { (millimeter) : [1, 2, 6] } as LengthBoundSpec);

        annotation { "Name" : "Rib inner gap at peak (datum)" }
        isLength(definition.ribGapAtPeak, { (millimeter) : [35, 40.2, 45] } as LengthBoundSpec);

        annotation { "Name" : "Per-side clearance (fit knob)" }
        isLength(definition.clearanceSide, { (millimeter) : [0, 0.15, 0.6] } as LengthBoundSpec);

        annotation { "Name" : "Rib length" }
        isLength(definition.ribLen, { (millimeter) : [15, 22, 40] } as LengthBoundSpec);

        annotation { "Name" : "Rib height" }
        isLength(definition.ribH, { (millimeter) : [1, 2, 2.6] } as LengthBoundSpec);

        annotation { "Name" : "Rib front position (+Y from center)" }
        isLength(definition.ribFrontY, { (millimeter) : [5, 18, 40] } as LengthBoundSpec);

        annotation { "Name" : "Slot width at front end" }
        isLength(definition.slotFrontW, { (millimeter) : [3, 4.0, 6] } as LengthBoundSpec);

        annotation { "Name" : "Slot peak width" }
        isLength(definition.slotPeakW, { (millimeter) : [3.5, 4.65, 6] } as LengthBoundSpec);

        annotation { "Name" : "Peak distance behind slot front" }
        isLength(definition.slotPeakD, { (millimeter) : [5, 8.85, 15] } as LengthBoundSpec);

        annotation { "Name" : "Taper slope (mm width per mm)" }
        isReal(definition.taperSlope, { (unitless) : [0.02, 0.10, 0.3] } as RealBoundSpec);

        annotation { "Name" : "Boss diameter" }
        isLength(definition.bossD, { (millimeter) : [10, 16, 30] } as LengthBoundSpec);

        annotation { "Name" : "Boss height" }
        isLength(definition.bossH, { (millimeter) : [4, 7, 15] } as LengthBoundSpec);

        annotation { "Name" : "Boss center behind rib front" }
        isLength(definition.bossBehindRibFront, { (millimeter) : [10, 21.85, 40] } as LengthBoundSpec);

        annotation { "Name" : "Thread major diameter (1/4-20 = 6.35)" }
        isLength(definition.threadMajor, { (millimeter) : [4, 6.35, 10] } as LengthBoundSpec);

        annotation { "Name" : "Thread diametral fit allowance" }
        isLength(definition.threadFit, { (millimeter) : [0, 0.3, 0.8] } as LengthBoundSpec);

        annotation { "Name" : "Socket depth (blind)" }
        isLength(definition.socketDepth, { (millimeter) : [5, 8, 12] } as LengthBoundSpec);
    }
    {
        const zPlate = definition.bossH;                 // plate bottom
        const zTop = zPlate + definition.plateT;         // fan base plane
        const bossY = definition.ribFrontY - definition.bossBehindRibFront;
        const zero = 0 * millimeter;

        // slot width at distance d behind the slot's front end (the kite profile)
        const slotWidthAt = function(d)
        {
            if (d <= definition.slotPeakD)
            {
                return definition.slotFrontW +
                    (definition.slotPeakW - definition.slotFrontW) * (d / definition.slotPeakD);
            }
            return definition.slotPeakW - definition.taperSlope * (d - definition.slotPeakD);
        };

        // plate
        fCuboid(context, id + "plate", {
                    "corner1" : vector(-definition.plateW / 2, -definition.plateD / 2, zPlate),
                    "corner2" : vector(definition.plateW / 2, definition.plateD / 2, zTop)
                });

        // boss (overlapped into the plate so the union is robust)
        fCylinder(context, id + "boss", {
                    "topCenter" : vector(zero, bossY, zPlate + definition.plateT / 2),
                    "bottomCenter" : vector(zero, bossY, zero),
                    "radius" : definition.bossD / 2
                });

        // ribs: one sketch with both kite outlines, extruded up from the plate top
        const ribPeakW = slotWidthAt(definition.slotPeakD) - 2 * definition.clearanceSide;
        const cx = definition.ribGapAtPeak / 2 + ribPeakW / 2;
        const stations = [zero, definition.slotPeakD, definition.ribLen];
        var ribSk = newSketchOnPlane(context, id + "ribSk", {
                    "sketchPlane" : plane(vector(zero, zero, zTop), vector(0, 0, 1))
                });
        for (var side in [-1, 1])
        {
            var pts = [];
            for (var d in stations)
            {
                const w = slotWidthAt(d) - 2 * definition.clearanceSide;
                pts = append(pts, vector(side * cx + w / 2, definition.ribFrontY - d));
            }
            for (var i = size(stations) - 1; i >= 0; i -= 1)
            {
                const w = slotWidthAt(stations[i]) - 2 * definition.clearanceSide;
                pts = append(pts, vector(side * cx - w / 2, definition.ribFrontY - stations[i]));
            }
            pts = append(pts, pts[0]);
            skPolyline(ribSk, "rib" ~ toString(side), { "points" : pts });
        }
        skSolve(ribSk);
        opExtrude(context, id + "ribs", {
                    "entities" : qSketchRegion(id + "ribSk", true),
                    "direction" : Z_DIRECTION,
                    "endBound" : BoundingType.BLIND,
                    "endDepth" : definition.ribH
                });

        // one solid
        opBoolean(context, id + "fuse", {
                    "tools" : qUnion([qCreatedBy(id + "plate", EntityType.BODY),
                                      qCreatedBy(id + "boss", EntityType.BODY),
                                      qCreatedBy(id + "ribs", EntityType.BODY)]),
                    "operationType" : BooleanOperationType.UNION
                });

        // FRONT marker notch, cut through the plate at the center of the front edge
        fCuboid(context, id + "notch", {
                    "corner1" : vector(-definition.notchW / 2,
                                       definition.plateD / 2 - definition.notchD,
                                       zPlate - 0.1 * millimeter),
                    "corner2" : vector(definition.notchW / 2,
                                       definition.plateD / 2 + 0.5 * millimeter,
                                       zTop + 0.1 * millimeter)
                });
        opBoolean(context, id + "notchCut", {
                    "tools" : qCreatedBy(id + "notch", EntityType.BODY),
                    "targets" : qCreatedBy(id + "plate", EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION
                });

        // tap-ready tripod bore (blind); the printed thread is modeled in sled.py
        fCylinder(context, id + "bore", {
                    "topCenter" : vector(zero, bossY, definition.socketDepth),
                    "bottomCenter" : vector(zero, bossY, -0.1 * millimeter),
                    "radius" : (definition.threadMajor + definition.threadFit) / 2
                });
        opBoolean(context, id + "boreCut", {
                    "tools" : qCreatedBy(id + "bore", EntityType.BODY),
                    "targets" : qCreatedBy(id + "plate", EntityType.BODY),
                    "operationType" : BooleanOperationType.SUBTRACTION
                });

        // No chamfers here on purpose: the bore-mouth lead-in and elephant's-foot
        // relief are print details owned by sled.py. Add them in Onshape with the
        // regular Chamfer tool on the bore mouth / boss rim if you want them here.

        opDeleteBodies(context, id + "delSk", {
                    "entities" : qCreatedBy(id + "ribSk", EntityType.BODY)
                });
        setProperty(context, {
                    "entities" : qCreatedBy(id + "plate", EntityType.BODY),
                    "propertyType" : PropertyType.NAME,
                    "value" : "apollo_sled"
                });
    });
