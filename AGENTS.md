# Little-Castle Assets repository rules

This local folder is the source-of-truth workspace for Little Castle art, not a Unity project. Legacy art binaries remain local. On 2026-10-08 the user explicitly authorized publishing the current versioned `Source/` and `Releases/` work through Git LFS for mobile/cloud continuation; see `docs/GITHUB_HANDOFF_2026-10-08.md`.

1. Read `README.md` and `docs/MIGRATION_MANIFEST.md` before moving, renaming, exporting, or deleting art.
2. Preserve the existing `Art/`, `Mat/`, `Scripts/`, `AssetsDatabase/`, `Content/` and `Config/` paths. Asset Book records depend on them. Do not move or rename these roots without an explicit catalog migration.
3. Existing legacy `Art/`, `Mat/` and Unreal binaries remain local, recorded in `docs/SOURCE_SNAPSHOT.sha256.csv`. Versioned `Source/` and `Releases/` binaries are the explicit user-authorized exception: commit them only through Git LFS and verify pointers before push. Never commit caches or recovery copies.
4. Do not edit an already-released game export in place. Validate a new local version, then create a reviewed versioned handoff package under `Releases/`. Copy a specific reviewed package into `Little-Castle/Assets/_Game/Art/Imported`; do not use symlinks/junctions between repositories.
5. Preserve stable asset IDs from `AssetBook/AssetBook.json`. Run the Asset Book sync/validation after catalog changes.
6. Legacy catalog: `python Scripts/asset_book.py validate-catalog` works without local binaries. New versioned catalog: `python Tools/sync_asset_book.py` after `git lfs pull`. Preserve both catalogs; merging legacy IDs requires a separate reviewed migration.
7. Unreal `.uasset`, `.umap`, `.uproject` and `Config/` are retained locally as historical reference only. Unity cannot import them.
