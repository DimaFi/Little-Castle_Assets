# Desktop art portability audit — 2026-10-08

## Scope and gate

**Published payload integrity: PASS.** The full verifier passed in the separate local/shared clone at commit `43dcae10e962659eceda7ea87786ca9f2b535c5b`; the integration workspace also passed before the grass dependency addition. The clone's release hashes, Git LFS OIDs/sizes, image/FBX/Blend signatures, catalogs, text bytes and bridge recipe passed. The clone was created from local Git/LFS storage, **not** an independent GitHub network clone. No released file was edited.

**Read-only Blender inspection: PASS for the reviewed Bridge v002 payload.** Blender 4.4.3 opened the clone's source `.blend` and imported all 13 v002 FBX files. The previously missing v001 grass preflight dependency was copied byte-for-byte into versioned `Source/Dependencies/Bridge_Stone_A/`; the updated clone hydrated and hash-verified its committed LFS pointer. **Rebuild portability remains unverified** because a complete rebuild was not attempted. Unity import, visual acceptance and profiling were not run.

The reviewed release may proceed to a controlled Unity import/visual test on its own package-integrity merits. It must not be described as a verified source rebuild or as Unity approved.

## Actual commands and results

Python: `C:/Users/Дмитрий/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`.

| Check | Result |
|---|---|
| `python -m unittest discover -s Tools -p 'test_portable_releases.py' -v` with `TEMP`/`TMP=E:\Games_Develop` | PASS, 10/10 fixtures, 0.736 s. The first run with the sandbox's default `%TEMP%` produced 9 fixture `PermissionError: [WinError 5]` setup errors because that sandbox temp path was not writable. This was an environment failure; no test logic failed after redirecting temp. |
| `python Tools/verify_portable_releases.py --json` in integration workspace | PASS, exit 0 after patches; `mode=FULL_LOCAL_VERIFICATION`, all 4 releases `status=PASS`. |
| Full `python Tools/verify_portable_releases.py --json` in updated local/shared clone | PASS, exit 0; 4 release manifests, 279 LFS paths, 173 unique objects, 392,137,389 unique bytes, 7 bridge recipe dependencies. Before fast-forwarding the clone, its pre-fix recipe produced `PORTABLE_AUDIT_FAILED: Absolute Windows drive path in bridge recipe: Source\Architecture\Bridge_Stone_A\v001\build_bridge.py`. The clone remained read-only during that initial check. |
| Same 10 unit fixtures in updated clone | PASS, 10/10, 0.748 s. |
| `python Tools/sync_asset_book.py` | PASS, 23 records; all files and dependencies resolved. |
| `python Scripts/asset_book.py validate-catalog` | PASS, 125 records, 0 errors, 0 unregistered candidate models. |

Verifier progression: first actual run failed with `PORTABLE_AUDIT_FAILED: v001: QA references missing texture: Meshes\..\Textures\T_WallStoneSurface_A_BaseColor.png`. `Tools/verify_portable_releases.py` now normalizes legacy FBX QA texture paths while rejecting paths that escape the release; `Tools/test_portable_releases.py` has a corresponding positive/negative regression fixture. The second run failed on the absolute bridge v001 reference path above. The bridge v001 builder now reads its versioned `References/Bridge_Concept.png`; the wall builder no longer reads an optional Downloads concept because its reference is already versioned. No geometry or release asset changed. After these patches, the integration-workspace full audit passed.

## Payload and Blender evidence

| Release | Manifest files | Hashed bytes | Result |
|---|---:|---:|---|
| `Bridge_Stone_A/v001` | 27 | 17,331,641 | PASS |
| `Bridge_Stone_A/v002` | 31 | 24,611,029 | PASS |
| `TerrainStarter-v001` | 16 | 12,821,109 | PASS |
| `Wall_Stone_Modular/v005` | 26 | 24,378,962 | PASS |

The verifier compared every release payload with its manifest SHA-256, each tracked versioned binary with its committed Git LFS pointer OID and size, and non-LFS release text with committed bytes. In the updated clone it reported **279 tracked LFS paths, 173 unique objects, 392,137,389 unique bytes**. This is one additional 22,716-byte grass dependency beyond the prior commit's 278 / 172 / 392,114,673. Bridge v002 sample SHA-256 values from the clone matched the published manifest:

| Payload | SHA-256 |
|---|---|
| Source `Bridge_Stone_A.blend` | `b0658a3427e81a5eb8929f084939efd335537d798e272924fa07c8af5087af3c` |
| `SM_Bridge_Stone_A_LOD0.fbx` | `b56f6628e802f39d8871c86a5393ee64c62d310eb517c08df48d2771a62da6f9` |
| `SM_Bridge_Stone_A_LOD1.fbx` | `47bff7db69aa2f7439fe5555de2bedaca63d9c160b292f329a36085cc9628f3c` |
| `SM_Bridge_Stone_A_LOD2.fbx` | `810df37ce397f50f4c3ac756b4b0c69449ee52db7c3e61005a808aa6396b0dd7` |

Blender opened the clone's Bridge v002 source with 31 mesh objects. All 6 used file images were packed, relative and resolvable. The 13 release FBXs all imported. Core bridge LOD0/1/2 had **13,598 / 7,704 / 1,736** triangles; dressing had **12,428 / 5,022 / 80**; collider had **286**. No imported mesh lacked UV layers. `Bridge_Sockets.fbx` intentionally contained 0 meshes and four empties: `RiverIn`, `RiverOut`, `RoadNorth`, `RoadSouth`. Blender emitted a non-fatal sandbox extension-cache permission warning while importing, but exited 0 with all QA records printed.

Each core bridge LOD imported as 5 mesh objects. The slot pattern is `SM_Bridge_FactionCloth_LOD{n}` → `M_Bridge_FactionCloth`, `SM_Bridge_Mortar_LOD{n}` → `M_Bridge_Palette`, `SM_Bridge_Stone_LOD{n}` → `M_Bridge_Stone`, `SM_Bridge_Trim_LOD{n}` → `M_Bridge_Palette`, and `SM_Bridge_Wood_LOD{n}` → `M_Bridge_Palette`. Across the package there are **6 authored material names**: `M_Bridge_FactionCloth`, `M_Bridge_Palette`, `M_Bridge_Stone`, `M_Bridge_Grass`, `M_Bridge_TerrainReference`, `M_Bridge_Water`. Four Unity materials are appropriate for the planned import scope: FactionCloth, Palette, Stone and Grass. Water and TerrainReference are intentionally excluded from that importer. The FBX slots confirm those assignments.

## Remaining portability limits

1. The v001 `preflight()` originally read local `CozySettlement/Art/Vegetation/Oak_Kit/Exports/SM_Grass_Short_A.fbx`, which bridge v002 invokes. The exact file is now at `Source/Dependencies/Bridge_Stone_A/SM_Grass_Short_A.fbx`: **22,716 bytes**, SHA-256 `60a7c654e15f72e5d28eb0997feb1194cdc80433f1eb70cdda8fb73d928d2edf`, matching the committed `docs/SOURCE_SNAPSHOT.sha256.csv` entry at line 535. The updated clone's committed pointer carried that OID/size and its hydrated payload matched. Blender imported the same copy as one 80-triangle mesh with UVs and `M_Oak_Kit_Palette`. The source rebuild itself was not run.
2. The wall builder's `prepare_inputs()` still optionally copies textures from local `CozySettlement/Mat/StoneWall_A_Unity` when rebuilding. Its versioned textures exist, and this audit did not rebuild the wall. That path deserves a separate source reproducibility review.
3. A network-fetched, freshly hydrated GitHub clone remains unverified. The local/shared clone confirms separation from ignored legacy files and that its hydrated payload bytes pass the audit phases above, but reused the same local Git/LFS object store.
4. Blender source opening and FBX imports do not establish rendered visual quality, Unity material/prefab setup, play-mode behavior or GPU cost. `unity_visual_approval=false` and `blender_rebuild_verified=false` remain accurate.
