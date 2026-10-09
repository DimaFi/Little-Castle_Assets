# Little Castle — CliffKit authoring prototype v001

Temporary Blender authoring accelerator. **NOT Unity runtime or approved game art.**

The complete ready-to-run bundle with **14 mesh archetypes × 3 LODs**, Blender generator, **17 PNG prototype material maps**, Python texture generator, source-only validator and Codex instructions is attached to the ChatGPT conversation as `LittleCastle_CliffKit_Codex_v001.zip`. The repository cannot ingest generated binaries directly without reviewed Git LFS art-release intake.

Codex: copy the ZIP's `Tools/CliffKit_Prototype_v001/` folder into this art repository at the same path. Open `CODEX_START_HERE.md` first. Run `python validate_pack.py`, then run Blender 4.4+ `-b --python build_cliff_kit.py -- --out Output` from that folder. **Blender and Unity have not been run in the creation environment.** Review normals, textures, LOD, geometry, and top/ground alignment before any Unity import. No approved release or player walkability is claimed.

Required integration rules:
- Read this repository's AGENTS.md, README.md, docs/MIGRATION_MANIFEST.md.
- Never put generator code in Unity runtime; leave it under source-art Tools and preserve as reproducible historical source.
- Do not change existing Unity Main profiles or global shaders, do not overwrite existing FBX releases.
- The gameplay heightfield controls passability; rock/cliff mesh is visual. Hike ramp candidates are ~15°; proposed infantry max 30°, carts 12° **subject to gameplay approval**. Ensure real terrain/nav connection and corridor clearance.
- Coordinate concept scarp decoration with game issue #37 (Q08), surface materials #36 (Q07), riverbank #38 (Q09). Use stable seed/feature IDs, respect road/river/bridge/start/building exclusions, never create gameplay stone resources from decorative rocks.
- Before publishing approved art, perform Blender visual QA, LOD optimization, create new immutable LFS source/release package, validate Asset Book, then isolated Unity importer/prefab/Player QA.
- See conversation archive for exact PNG manifest/checksums. Python source-only checks: 17 texture maps and 42 geometry variants; **no Blender export tests**.
