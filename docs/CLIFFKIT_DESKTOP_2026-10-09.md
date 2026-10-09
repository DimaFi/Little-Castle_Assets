# CliffKit v001: desktop authoring and Unity intake

User-supplied pack: `LittleCastle_CliffKit_Codex_v001/CliffKit_Prototype_v001`.
Read CODEX_START_HERE and all scripts/maps, GitHub prototype handoff60521f7 and
game Q08 issue37 (no comments). The two supplied world concepts were found in
the authorized conversation “Генерация мира ассетов” and archived as references.

Work was isolated in branches `codex/cliff-kit-v001` (art) and
`codex/cliff-kit-intake-v001` (game), leaving the existing checkouts untouched.
No agents were delegated. Original Blender prototype is retained under Tools;
original17 PNGs and their manifest remain byte-preserved under Source. Prototype
default texture paths still describe its original bundle; use the new recipe
for the published source layout. No Tools/.blend files entered the Unity build.

Source: [README](../Source/Environment/CliffKit/v001/README_RU.md),
[actual 42-mesh/FBX QA](../Source/Environment/CliffKit/v001/QA/geometry.json),
[texture/seam contract](../Source/Environment/CliffKit/v001/QA/source_contract.json),
[portable audit](../Source/Environment/CliffKit/v001/QA/portable_audit.json).

Blender4.4.3/802179c51ccc executed, not inferred from Python. All42 meshes have
closed surfaces, outward normals, usable UVs and positive volume; all42 FBXs
roundtrip within0.1mm. Geometry changes were iterated after actual Cycles renders:
less regular buttresses, varied crest, and retained far silhouette. 70 final
renders show every type in3LOD andfront/rear. Same-height module boundaries
share positions; different heights/curves require their own terrain contact.

![Actual archetypes](../Source/Environment/CliffKit/v001/QA/ARCHETYPES.jpg)

Eight cliffs924/272/170 triangles each; four rocks192/96/64; ramps576/192/108.
Source remains an art candidate with prototype maps, not a claim of final
concept-level weathering/moss, production terrain blending or measured FPS.
AO_Approx is not mesh baked; Height/MossMask are source-only in this release.

Immutable release `Releases/CliffKit/v001`:55 files/4,404,719bytes; source commit
`7dcd0945b507d4b78e620d5afd8a0cfedf2915c3`; release commit `7d71b6c`.
Release manifest SHA256:
`6caf39663fb6c7c2956b620add0fdf20afde30b95900013b5850eb78782fcff0`.
Texture manifest SHA256:
`db4bb35eabdddbc2b8960467bda1fd0ef7d7ac55dd4957cbdf839056801d8739`.
New Asset Book adds14 distinct IDs; all37 records validate; legacy IDs remain.
All versioned binaries use LFS. Original portability test suite10/10 and the
complete/partial CliffKit intake test passed. The existing catalog count guard
was minimally extended from23 to23+complete14; hash/path/pointer checks remain.

Actual Unity6000.5.5f1 intake produced14LOD prefabs and a separate catalog.
It caught FBX handedness: final prefabs compose180° yaw with the original axis
rotation. An attempted replacement of that rotation failed measured bounds;
the corrected composition passed. Dedicated GPU fixture ran on RTX4070TiSUPER,
day/night andsame-height2-module joins at3LOD; distant brightness was tuned
without editing shared shaders. EditMode187/187, PlayMode5/5 passed on final
code/prefab bytes at game commit`5c069b85d7fd67ebb2ff33b4cbfa6c3ffe06ed3c`.

Game report `docs/reports/cliff-kit-v001-intake-2026-10-09.md` contains actual
XML, bounds, GPU fixture images, diagnostic failures and Q08 integration contract.
Four saved source-terrain seeds confirmed negative borders/repeatability;
naive fixed-height cliff/ramp footprints were refused on all four probes.
Macro plan/masks were not supplied. Real generated placement, terrain palette,
infantry/cart nav/clearance, eviction/IDs and actual Player profiling remain
BLOCKED/NOT_RUN. Q08/WorldStreamer/catalog/terrain heights ownership is preserved.
No decorative stone resources, foliage shader change, full-map GameObjects,
fake village or automatic production merge.

Build/QA logs are archived in Source/Environment/CliffKit/v001/QA. Recipes:
`build.py`, `qa_render.py`, `verify.py`, `package.py`, `collect_evidence.py` in
Tools/CliffKit_v001. To revise published geometry createv002; do not overwritev001.
