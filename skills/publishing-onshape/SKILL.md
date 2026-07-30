---
name: publishing-onshape
description: >-
  Publishes parts to Onshape as NATIVE feature trees via the REST API - real
  sketches and extrudes the user can click and edit in the Onshape editor, not
  STEP imports or custom-feature dials. Use when the user wants a part in
  Onshape in fully editable form, or asks to push/publish CAD to Onshape.
---

# Publishing native feature trees to Onshape

STEP import gives Onshape a dumb solid; a FeatureScript custom feature gives one
dialog node. When the user wants a *real tree* - Sketch 1, Extrude 1, every step
clickable - build the features through the REST API with
`scripts/publish_sled_native.py` as the template.

## Workflow when the user asks to publish a part
1. Start from the part's build123d source (the print pipeline's source of truth)
   and compute the expected final volume locally - it is the end-to-end check.
2. Copy `scripts/publish_sled_native.py` and rewrite `build_plan()` for the
   part: every sketch goes on a default plane referenced BY NAME (Top/Front/
   Right), geometry in meters, extrudes BLIND with an explicit up/down flag.
   Order: the base `NEW` extrude first - the main loop anchors every later
   boolean's merge scope to its body automatically.
3. Features that would need to start mid-solid (a blind pocket entered from the
   far side) are a through-cut plus a re-added cap - see "Design for
   editability" below.
4. `--dry-run` first (zero API calls), then run. New document by default;
   `--url <document URL>` builds into an existing one instead.
5. Report back: document URL, volume match, feature statuses, and the run's
   API-call count.

## Editing an already-published document
Small dimension tweaks are cheapest done by the user in the Onshape UI (zero
API calls). For agent-driven edits: GET `/features`, modify the feature's JSON
(parameters or sketch entities), POST it back to
`/features/featureid/{featureId}` with the same `BTFeatureDefinitionCall-1406`
wrapper; batch several edits through `/features/updates` in one call. Never
delete-and-recreate a document to change a parameter.

## Auth
API keys (HTTP Basic) from `~/.config/onshape/credentials`
(`ONSHAPE_ACCESS_KEY=` / `ONSHAPE_SECRET_KEY=` lines) or env vars; created at
https://cad.onshape.com/appstore/dev-portal. `onshape_client.py` loads them and
never logs values. Keys may lack the delete scope ("Invalid API key state" on
DELETE) - reuse documents with `--url` instead of recreating.

## Payload rules that cost a debugging session (do not rediscover)
- POST `/api/v6/partstudios/d/{did}/w/{wid}/e/{eid}/features` with body
  `{"btType": "BTFeatureDefinitionCall-1406", "feature": {...}}`.
- Parameter query lists are `BTMParameterQueryList-148` (not -67).
- Reference default planes by NAME, not deterministic id:
  `BTMIndividualQuery-138` with
  `"queryString": "query=qCreatedBy(makeId(\"Top\"), EntityType.FACE);"`.
- Extrude regions: `BTMIndividualSketchRegionQuery-140` with the sketch's
  `featureId` from the add-feature response.
- Sketch geometry is in METERS. Lines: `BTMSketchCurveSegment-155` with
  `BTCurveGeometryLine-117` (pnt + dir = full delta, params 0..1). Circles:
  `BTMSketchCurve-4` with `BTCurveGeometryCircle-115`.
- The featurescript endpoint takes `"queries": {}` (a map, not a list).
- Sketch ARCS: `BTMSketchCurveSegment-155` wrapping `BTCurveGeometryCircle-115`
  with `startParam`/`endParam` in RADIANS (CCW from +x with `xDir:1,yDir:0,
  clockwise:false`); lines use 0..1 params. Rounded rects = 4 lines + 4 quarter
  arcs, endpoints numerically coincident, constraints [].
- Extrude draft: add `hasDraft` (bool), `draftAngle` (quantity, "1 deg"),
  `draftPullDirection` (bool; false narrows an UP extrude going up). Onshape
  measures draft from the SKETCH PLANE, not the extrude's functional start -
  compensate the profile by 2*offset*tan(angle) when the part's draft datum
  sits above z=0.
- Chamfer: featureType "chamfer", params `entities` (query list),
  `chamferType` enum `EQUAL_OFFSETS` (enumName "ChamferType"), `width`
  quantity, `tangentPropagation` bool. Concave edges work (adds material).
  Select edges with `qContainsPoint(qEverything(EntityType.EDGE), vector(...)
  * meter)` - one seed point per tangent chain; qCreatedBy on the extrude that
  formed a boolean edge can come up empty, qEverything+point is the robust
  form. Verify via featureState + a mass-properties closure, not the
  featurescript eval endpoint (it can report 0 for edges that features
  resolve fine).
- Failed features stay addressable: POST the corrected definition back to
  `/features/featureid/{fid}` (same wrapper) instead of deleting.

## Design for editability
Keep every sketch on a default plane (no face-id discovery, no fragile
references). Reach features that would need a mid-solid start (e.g. a blind
socket entered from the far side) via a through-cut plus a re-added cap - two
plain features that read sensibly in the tree. Print-prep details (chamfers,
modeled threads) stay in the build123d source; the user adds cosmetic ones with
native tools if wanted.

## Verify
Each add-feature POST response carries that feature's `featureState` - check it
there and fail fast; no trailing GET `/features` sweep needed. Then one GET
`/massproperties` compares volume against the build123d part's (computed
exactly; tolerance covers only intentional deltas like omitted
chamfers/threads). Report the document URL.

## API frugality
Onshape API keys are rate-limited per minute, not billed per call - conserve
for speed and headroom, not cost. A full publish should be ~13 calls: create +
elements + one POST per sketch/extrude + one massproperties. Rules: validate
plans locally first (--dry-run costs zero calls); read feature status from POST
responses, never a follow-up GET; batch multi-feature edits through the
features/updates endpoint instead of one POST per feature; reuse documents via
--url rather than create-and-abandon; and never re-derive the payload rules
above by trial against the server.
