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

## Mobile/cloud handoff — 2026-10-08

The user explicitly requested publishing current work. `Source/`, `Releases/`,
`AssetBook/` and `Tools/` are now versioned alongside the preserved legacy tree.
New source/release art binaries use Git LFS; run `git lfs pull` after cloning.
Legacy `Art/`, `Mat/` and Unreal binary libraries remain local-only. See
[handoff scope](docs/GITHUB_HANDOFF_2026-10-08.md). Released v001/v002 bridge
packages and v004/v005 wall packages must remain immutable.
