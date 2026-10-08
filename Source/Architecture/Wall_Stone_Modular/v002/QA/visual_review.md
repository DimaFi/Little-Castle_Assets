# Visual inspection — v002 — 2026-10-02

Status: author inspection complete; user aesthetic acceptance PENDING.
This record does not authorize publishing a release or importing Unity.

Inspected actual Blender renders, not image-generated model illustrations:

- Stone_and_Banner_Closeup: real joint shadows, staggered courses, separate
  bevelled blocks, unobstructed white banner. Rejected intermediate texture
  sampling looked blurry; replaced by shared grout-free albedo.
- QA_Clay_Closeup: all major stone relief survives removal of the texture.
- Kit_Overview: four stone modules and separate cloth/bracket, intact framing.
- Wall_Modular_Preview: straight and gently turning rigid segments. This is
  hand-assembled QA, not runtime path-placement acceptance.
- QA_Mixed_and_Sharp: mixed lengths, finished end and pillar-covered 90° turn.
- QA_LOD_Comparison: LOD0 right, LOD1 middle, LOD2 left. Initial LOD2 flat slab
  rejected during inspection; final LOD2 retains block courses and joints.
- QA_Player_Colours: blue, red, green and ochre test variants.
- QA_Banner_PNG_LODs: asymmetric F image remains correctly oriented across
  the three cloth LODs. Demo image is not exported as a fixed faction design.

The studio appearance is lighter/cleaner than the illustrated settlement
reference. It is not a pixel-identical reproduction of that drawing; user
review should judge the new stone shape, palette and degree of weathering.
No vegetation, moss props or baked faction emblem have been added.

Independent binary FBX validation: PASS (export_validation.json).
Stone triangles LOD0/1/2: 2m 3684/1508/408; 1m 3468/1420/392;
pillar 2794/1258/346; end 2292/1012/276.
Cloth 384/96/24; bracket 300/60/36. Source and exported coordinates match.

Not tested: Unity import/material matching, gameplay placement, LODGroup
screen thresholds, actual corner/tower replacement runtime or performance.
