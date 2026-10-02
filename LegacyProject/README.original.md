# Cozy Settlement — cottage test

Open `CozySettlement.uproject` with Unreal Engine 5.7.3. Startup map: `/Game/Maps/CottageTest`.

## Current result

- Cottage v3: curved gable infill, revised dormer junction, simplified entrance lintel.
- Editable Blender source: `Art/Cottage/Cottage_03_editable.blend`.
- Combined mesh with UVs: `Art/Cottage/Cottage_03.fbx`.
- Blender QA views: `Cottage_03_front.png`, `Cottage_03_rear.png`, `Cottage_03_roof.png`.
- Imported mesh: `/Game/Art/Cottage/Cottage_03`; three instances in the test map.
- Unreal recomputes normals and tangents, removes degenerates; simple box collision is applied.
- Automated level reload and house-count assertion passed. This does not prove visual quality or performance.
- Project-local filesystem DDC avoids the failing Zen service on this machine. Engine-wide settings were not edited.

## Remaining validation

Inspect rendered Unreal viewport close up and at strategy distance. Check roof junctions, shading, materials and collisions. Measure performance before claiming a budget. Ground is a flat test platform, not Landscape; slope placement, terrain adaptation and player-controlled zoom are not implemented yet. Materials remain flat-color prototypes. Editable source is saved before merged-mesh UV preparation; rerun v3 script for exports.

## Repeatable workflow

1. Edit Blender source or generator; preserve previous versions.
2. Generate front, back and overhead renders; inspect roof, openings and base.
3. Export a combined FBX with meter-to-centimeter conversion and an origin at the base.
4. Run `Scripts/setup_scene.py` through Unreal Python only when intentionally rebuilding the test map (it replaces that map).
5. Run `Scripts/validate_scene.py` to set mesh build/collision options and reload-check the map.
6. Inspect actual Unreal rendering; then test slope placement and frame time.
