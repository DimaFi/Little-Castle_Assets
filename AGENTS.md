# Little-Castle Assets repository rules

This repository is the source-of-truth for Little Castle art, not a Unity project.

1. Read `README.md` and `docs/MIGRATION_MANIFEST.md` before moving, renaming, exporting, or deleting art.
2. Keep editable Blender source, references, QA evidence, build scripts, and the Asset Book here. Never put Unity `.meta`, `Library`, `Temp`, or generated engine caches here.
3. Do not edit an already-released game export in place. Create a new version in `Source/`, validate it, then publish a reviewed FBX/texture package in `Releases/`.
4. `Releases/` is the only directory Unity may consume. Copy a specific reviewed release into `Little-Castle/Assets/_Game/Art/Imported`; do not use symlinks/junctions between repositories.
5. Preserve stable asset IDs from `AssetBook/AssetBook.json`. Run the Asset Book sync/validation after catalog changes.
6. Binary art files are Git LFS files. Verify `git lfs install` before the first large import and verify pointers before pushing.
7. Unreal `.uasset` and `.umap` files are retained only in `Legacy/Unreal/` as historical reference. Unity cannot import them.
