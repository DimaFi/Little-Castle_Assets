# Little-Castle Assets repository rules

This local folder is the source-of-truth workspace for Little Castle art, not a Unity project. Its GitHub repository deliberately contains only lightweight reproducibility data; large art binaries remain local.

1. Read `README.md` and `docs/MIGRATION_MANIFEST.md` before moving, renaming, exporting, or deleting art.
2. Preserve the existing `Art/`, `Mat/`, `Scripts/`, `AssetsDatabase/`, `Content/` and `Config/` paths. Asset Book records depend on them. Do not move or rename these roots without an explicit catalog migration.
3. Editable Blender source, FBX exports, textures, references, QA evidence and build scripts live here locally. Never add heavy binary art files to GitHub. Their snapshot is `docs/SOURCE_SNAPSHOT.sha256.csv`.
4. Do not edit an already-released game export in place. Validate a new local version, then create a reviewed Unity handoff package outside Git tracking. Copy a specific reviewed package into `Little-Castle/Assets/_Game/Art/Imported`; do not use symlinks/junctions between repositories.
5. Preserve stable asset IDs from `AssetBook/AssetBook.json`. Run the Asset Book sync/validation after catalog changes.
6. Use `python Scripts/asset_book.py validate` in this local workspace. A lightweight GitHub clone uses `python Scripts/asset_book.py validate-catalog` because the binary source files are intentionally absent there.
7. Unreal `.uasset`, `.umap`, `.uproject` and `Config/` are retained locally as historical reference only. Unity cannot import them.
