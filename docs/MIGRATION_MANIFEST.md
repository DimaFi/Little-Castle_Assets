# Initial source-art migration manifest

Status: **planned; no source asset has been copied yet.**

Source snapshot audited on 2026-10-02: `E:\Games_Develop\CozySettlement`. The destination is this repository, cloned at `E:\Games_Develop\Little-Castle_Assets`. The Unity game repository is `E:\Games_Develop\Little-Castle`.

## Boundary contract

| Repository | Owns | Must not own |
|---|---|---|
| `Little-Castle_Assets` | Blender source, source textures, references, art scripts, asset catalog, QA, renders and reviewed export releases | Unity project metadata, runtime code, Unity scenes, `Library` |
| `Little-Castle` | Unity code, ScriptableObjects, prefabs, Unity materials and explicitly approved game-ready copied imports | `.blend` working files, art WIP, build logs, Unreal cache/data |

There is no folder link, junction, package dependency, or live import between repositories. It would let Unity write `.meta` files into the source repository and would make builds machine-path dependent. A release is copied by a deliberate, reviewable commit.

## Audited transfer inventory

The following authored files are to be preserved. Counts include source, reference, QA and export evidence.

| Source collection | Destination | Files / size | Contents | Transfer disposition |
|---|---:|---:|---|---|
| `Art/Cottage` | `Source/Architecture/Cottage_01_03` | 18 / 36.7 MiB | Cottage 01–03 Blender files, FBX, previews, build scripts | transfer all except `.blend1` recovery copies |
| `Art/House_Cottage_A` | `Source/Architecture/House_Cottage_A` | 494 / 1.65 GiB | house, courtyard, roof, openings, timber, yard kit, 22 modules, docs, QA, references, renders, scripts | transfer all authored sources, docs, JSON QA, renders and scripts; exclude transient `.log` files only after their useful JSON/visual evidence is verified |
| `Art/Props` | `Source/Props/Standalone` | 10 / 4.7 MiB | Birdhouse, Lantern, Blender sources, FBX, previews, script, README | transfer all except `.blend1` recovery copies |
| `Art/Vegetation` | `Source/Vegetation` | 225 / 597.9 MiB | Oak Kit, Tree_01–04, Tree02, LOD exports, foliage/ground modules, texture sets, validation and render evidence | transfer all authored sources/exports/textures/docs/QA; omit `.blend1` recovery copies and disposable `.log` files after audit |
| `Mat` | `Materials/PBR` | 146 / 406.9 MiB | 17 texture families: bark, timber, plaster, roof, terrain, foliage, rocks, etc. | transfer all `.png`, `.jpg`, `.exr` and descriptive text; keep source channel naming |
| `Scripts` | `Tools/LegacyAndCatalog` | 3 Python scripts / 42 KiB | `asset_book.py`, `setup_scene.py`, `validate_scene.py` | transfer `.py`; do not transfer `__pycache__` |
| `AssetsDatabase` | `AssetBook` | 2 / 164 KiB | `AssetBook.json`, generated `AssetBook.md`, 125 registered records (123 Ready, 2 InProgress) | transfer both; preserve IDs and update relative paths |
| `Content` | `Legacy/Unreal/Content` | 20 `.uasset` / 3.1 MiB | Cottage mesh/material assets | archive as legacy reference only; never import into Unity |
| `Content/Maps/CottageTest.umap` | `Legacy/Unreal/Maps` | 1 / small | historical Unreal test map | archive only; recreate Unity test scenes separately |
| `Config/DefaultEngine.ini`, `Config/DefaultInput.ini` | `Legacy/Unreal/Config` | 2 / 9.7 KiB | historical Unreal settings | archive only; no Unity effect |

The audit covers **921 files / approximately 2.67 GiB** across the authored and legacy roots. It includes 12 Blender recovery files, 76 transient logs and 1 Python bytecode file; the initial source transfer baseline is therefore **832 files**, plus only those named QA logs whose JSON or visual record needs them. All large binary files use Git LFS.

## Asset roster to preserve

### Architecture

- `Cottage_01`, `Cottage_02`, `Cottage_03` source/exports.
- `House_Cottage_A`: current master house, courtyard assembly, roof history, foundation, masonry, plaster, timber frame, doors, windows, dormer and chimney work.
- Yard modules: Barrel, Birdhouse, Bucket, Crate, FenceBay, FlowerBox, Gate, LogStack, Pot, Signpost, StoneWall, StumpAxe, Well, Wheelbarrow, WoodBench, Woodshed and WoodTable.
- The `CURRENT.json` dependency map, module catalogue, material docs, QA manifests and checkpoint renders are part of the source of truth.

### Vegetation and terrain dressing

- Oak Kit: trunk/root/canopy source, LOD0–LOD2 tree, branch, leaf, flower, grass, ground patch and stone module exports.
- `Tree_01`, reference trees 02/03, packaged `Tree_04` with LODs, lantern/birdhouse attachments and bark/foliage textures.
- `Tree02` blockout/wood stages, validation reports and renders.

### Standalone props and materials

- Standalone Birdhouse and Lantern.
- PBR groups: `Bark`, `DoorWood`, `Logs_Bark`, `Material_terrain`, `Packed`, `RoofTile`, `Shutters`, `T_ChimneyStone`, `T_FieldStone`, `T_Foliage`, `T_Plaster`, `T_Timber`, `Tree02_Bark`, `Tree02_Leaves`, `Tree02_Moss`, `Tree02_Rocks`, and existing test texture groups.
- Base Color, Normal, Roughness/Gloss, AO, Height/Displacement and EXR source maps are retained. Channel packing for Unity happens only in a reviewed release.

## Explicit exclusions

Never copy these into either Git repository as source assets:

- `DerivedDataCache/`, `Intermediate/`, `Saved/` and Unreal webcache/shader cache;
- `__pycache__/`, `.pyc`, Blender automatic recovery files (`.blend1`, `.blend2`, etc.);
- editor logs and one-off generated scratch files unless a named QA record depends on them;
- Unity `Library/`, `Temp/`, `Logs/`, `UserSettings/` and `.meta` files in this source repository.

## Safe execution order

1. Commit this repository skeleton and configure Git LFS.
2. Copy the listed authored roots into their destination folders without deleting or moving anything from `CozySettlement`.
3. Compare file count, byte count and SHA-256 manifest between source and destination; report exclusions separately.
4. Repair Asset Book relative links, run its sync command, and validate every registered source path.
5. Commit the provenance import to `Little-Castle_Assets`; push it before touching the Unity repository.
6. For each finished game asset, create `Releases/<AssetId>/<version>/` containing FBX, textures, a release manifest and preview.
7. Copy only a reviewed release into `Little-Castle/Assets/_Game/Art/Imported/`; create Unity materials/prefabs there and link it through `WorldSpawnCatalog`.
8. Run Unity compilation, deterministic generation tests and streaming tests. An art import must not alter authoritative generated world data.

## Release acceptance checklist

Each `Releases/<AssetId>/<version>/release.json` must record source path and commit, asset ID, Blender version, export date, triangle/LOD counts, texture set, units, pivot, collider intention and a preview image. Before copying to Unity verify applied transforms, Y-up conversion, scale in metres, normal/UV validity, material naming, LOD order and texture import intent.

The game-side import is accepted only after the prefab is visible at correct scale, the world generation test passes for multiple seeds and negative chunks, and streaming unload removes its runtime instances cleanly.
