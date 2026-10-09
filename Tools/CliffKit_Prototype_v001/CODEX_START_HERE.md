# Little Castle — CliffKit Prototype v001 (Codex: START HERE)

**Status:** temporary authoring accelerator, **not approved runtime content**. Made 2026-10-09. The kit creates candidate art to be visually reviewed, optimized and eventually rebuilt/retouched by Blender artists. The actual Unity map generator, enemy/player accessibility, resource policy and navigation remain separately owned.

## Ownership and repository boundaries

- **Source art home:** `DimaFi/Little-Castle_Assets`, isolated `Tools/CliffKit_Prototype_v001`. This code runs **only in Blender/normal Python**, not in a Unity build.
- **No generated FBX/.blend in the game repo** without a new reviewed versioned `Source/` and `Releases/` art intake using Git LFS, manifest + SHA-256 verification and fresh Unity prefab/LOD/material checks.
- Existing production art, terrain generation profiles, shader `LC_Terrain`, vegetation `LC_Foliage`, `Main*` and Unity scene **are not changed by this kit**. Do not overwrite or auto-sync assets.
- Project requires Built-in rendering on current concept branch (Unity 6000.5.5f1). **Do not migrate to URP just to use this kit.** Read both `AGENTS.md` and the actual current integration branch before making changes.
- This kit belongs to a disposable/prototype **authoring tool** track. After handoff, archive versioned scripts in source-art repository; remove prototypes only when approved asset sources and reproducing instructions are preserved. Never delete accepted source history automatically.

## Inventory: 14 archetypes × LOD0/LOD1/LOD2

**Cliff:** `Cliff_Straight_A/B`, `Cliff_Convex_A`, `Cliff_Concave_A`, `Cliff_Terrace_Low/High`, `Cliff_End_Left/Right` — cliff face with grassy upper cap that overlaps the *high* terrain. Top must be matched to terrain by Unity placement/heightfield adjustment, not by arbitrary offsets.

**Rocks:** `Rock_Outcrop_Large/Medium`, `Rock_Boulder_Small/Large` — standalone exposed stones. Rocks are **decoration only**; stone/metal resources are separate authoritative world data.

**Foot-only ascents:** `Ramp_Hike_A/B` — visual sloped green path edged by rock, ascending along local **+Z**. Nominal gradients ≈15.15° / 15.71° respectively. For infantry-only access, Unity must have a matching real terrain walk surface with clearance, and classify agents/routes by slope. These FBXs do not add gameplay navigability themselves.

## Texture package

Required in `Textures/`:
- `Rock_Limestone_A/{BaseColor,Normal_OpenGL,Roughness,Height,AO_Approx,MossMask}.png`
- `Rock_Limestone_B/{BaseColor,Normal_OpenGL,Roughness,Height,AO_Approx,MossMask}.png`
- `GrassCap_A/{BaseColor,Normal_OpenGL,Roughness,Height,AO_Approx}.png`
- `Textures/TEXTURE_MANIFEST.json`: file SHA-256 hashes, size, seed.

All 17 PNG maps are generated as a deterministic **tileable prototype**, with OpenGL +Y normal convention. **AO_Approx is a procedural cavity approximation, not mesh-baked AO**. Height map is not a sculpt displacement automatically. Roughness is NOT Unity Built-in Standard smoothness; invert it only in an approved Unity material packing process. MossMask is a blending suggestion; no expectation of automatic FBX-to-Unity ShaderNode export. No metallic channel is needed for nonmetallic limestone/grass. Some textures may need art-directed repainting and mip/filter/alpha checks before production.

## How Codex should run the pack (Windows examples)

Install Python 3 with Pillow and NumPy (optional if PNGs already downloaded):

```powershell
py -m pip install numpy pillow
py Tools/CliffKit_Prototype_v001/generate_textures.py --size 1024
py Tools/CliffKit_Prototype_v001/validate_pack.py
```

Run with actual Blender (4.4.3 was used on previous desktop runs; this prototype has **not** been executed in Blender here):

```powershell
& 'C:\Program Files\Blender Foundation\Blender 4.4\blender.exe' -b --python 'Tools/CliffKit_Prototype_v001/build_cliff_kit.py' -- --out 'Tools/CliffKit_Prototype_v001/Output' --seed 20261009
```

Adjust the path to Blender. Output should contain `CliffKit_AUTHORING.blend`, one FBX per archetype/LOD (42 candidate FBX files), and `ASSET_CATALOG.json`. All binaries are **local generated output** until separately reviewed and published via Git LFS. Script can build one model with `--only Cliff_Straight_A`.

## Visual QA (do not claim PASS from Python tests)

1. Inspect each FBX in **Blender** (dimensions, pivot, object transforms, face normals, UV continuity, rock moss spots, grass cap, at least 3 camera angles). Compare to supplied two stylized screenshots. Improve silhouette/edge breakup and eliminate repeated or vertical tile artifacts by authoring if required.
2. Inspect 0.5m / 3m / 15m / 40m from the model. LOD0→1→2 should remain recognizable. No geometric cracks at top, side or terrace seams, no visible lower skirt intersection, no stretched rock texture or black material import.
3. Test two face modules end to end and an adjacent ramp. Do **not** assume automatic snap/tessellation: establish snap sockets, mesh dimensions, edge blending, instance scale and consistent facing. Verify clipping against the actual heightfield.
4. Check real project `TerrainSurfaceStage`, `StylizedLandformSampler`, scarp mask and world `WorldStreamer` flags. Design **optional concept-only** deterministic scarp-decorator instances. Reserve nav and construction corridors before scatter; stable IDs from seed and world coords; no entity spawns for decorative grass. No double-spawn after chunk eviction/revisit.
5. High ground must be the real gameplay heightfield. Decorative cliff front should hide the steep transition; the cap merely masks seams. The lower terrain and upper terrain must connect using a **shared heightfield policy** sampled in world coordinates. A heightfield cannot create overhangs; a rock mesh can, but must be treated as decoration/non-walkable unless separately supported.
6. Ramp placement: terrain path segment must actually satisfy slope/walk width; identify passable cells for infantry (initial *design suggestion* ≤30°) and carts (≤12°, to be agreed with existing navigation/vehicle controllers). Actual ramp grade ~15° allows infantry but not carts under these thresholds. Terrain clearance, climb animation/pathfinding, slope samples and exit connections are required. No nav on vertical cliff faces. Don't silently modify core game rules without root approval.
7. Keep harvestable rocks/deposits authoritative; decorative rock density must never change resource fairness or spawns. Avoid blocking roads, roads' bridge sockets, construction footprints, strategic exits or village entrances.
8. Import into isolated Unity concept art catalog on a new branch only after source QA, assigning a common terrain-compatible limestone shader/material (one or two shared rock materials), cap material, proper LODGroup, sensible collider (not high-poly MeshCollider every rock), GPU instancing eligibility, and documented pivot/orientation. Measure near/far draw calls, shadows and streaming spikes in actual Player. **No automatic production merge.**

## Recommended architecture (not implemented by this tool)

```text
WorldSeed + preset
  -> world-space highland/scarp mask + slope/buildability
  -> approved cliff archetype and stable placement record (NO Unity objects)
  -> validate upper/lower ground support, ramp grade, corridor/river exclusions
  -> optional heightfield contact blending/stamp in stage, deterministic cross-chunk
  -> streamed chunk presentation: approved FBX prefab, authored LODGroup
  -> per-quality presentation budget + actual GPU Player profile
```

**Important:** current concept GitHub queue already has Q08 `ScarpDecorationStage` (issue #37), Q07 terrain material (issue #36), Q09 riverbank decoration (issue #38). Coordinate ownership before integration; use these issues, do not build a competing renderer/stage. `WorldStreamer`, scenes and material catalogs belong to the root integrator unless ownership is transferred.

## Acceptance report and deprecation

Codex must produce `docs/reports/cliff-kit-v001-intake-YYYY-MM-DD.md` in the **game repo** with exact git SHAs, texture manifest SHA-256, Blender version/logs, thumbnail contact sheet, Unity prefab count/LOD bounds, actual slope/walk/cart checks at real seeded hills, negative chunk seams, screenshots close/far/day/night, collision and GPU measurements, explicit PASS/FAIL/BLOCKED. Need at least one fail-case invalid cliff footprint and no fake fixed-spawn village. Keep any approved Blender sources and FBX release immutable. When the approved kit replaces these prototypes, Codex may remove the prototype *from the Unity game import*, but keep script in source-art history/archive for reproducibility.

## Limitations of this deliverable

`generate_textures.py` and `validate_pack.py` were run with Python. Three procedural geometry generators were checked source-only on 14 archetypes × 3 LODs; Blender was **not available** in the creation environment. FBX export, Unity imports, nav, appearance, quality/performance, correct alpha/mips and seamless cross-mesh placement are **PENDING REAL DESKTOP TESTING**. These are candidate meshes/materials, not guaranteed matching final screenshots.
