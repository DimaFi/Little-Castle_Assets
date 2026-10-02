# Little Castle — Art Sources

This is the separate local source-art workspace for **Little Castle**. It contains editable Blender files, textures, asset documentation, build/validation scripts, reference renders, QA evidence, and historical Unreal reference data.

The game repository is [DimaFi/Little-Castle](https://github.com/DimaFi/Little-Castle). It contains Unity code, settings, scenes, and only approved game-ready imports. It must not contain working `.blend` files, intermediate renders, or the historical Unreal project. The GitHub repository for this workspace tracks only the Asset Book, scripts, documentation and file-hash snapshot; large art binaries are intentionally local-only.

## Repository layout

```text
Art/             editable Blender sources, exports, references, QA and renders
Mat/             authored source PBR texture sets
AssetsDatabase/  canonical Asset Book inventory and reuse process
Scripts/         Asset Book maintenance and art build/validation scripts
Content/, Config/, *.uproject  local Unreal reference only; not Unity-importable
docs/            pipeline, migration manifest and complete SHA-256 source snapshot
```

Read [the migration manifest](docs/MIGRATION_MANIFEST.md) before a handoff to Unity. The source tree is intentionally independent of Unity: Unity consumes reviewed copied releases, never a live linked folder.
