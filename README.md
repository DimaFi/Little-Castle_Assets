# Little Castle — Art Sources

This is the separate source-art repository for **Little Castle**. It contains editable Blender files, textures, asset documentation, build/validation scripts, reference renders, QA evidence, and historical Unreal reference data.

The game repository is [DimaFi/Little-Castle](https://github.com/DimaFi/Little-Castle). It contains Unity code, settings, scenes, and only approved game-ready imports. It must not contain working `.blend` files, intermediate renders, or the historical Unreal project.

## Repository layout

```text
AssetBook/       canonical asset IDs, inventory and reuse process
Source/          editable Blender sources, scripts, references, QA and renders
Materials/       authored source PBR texture sets
Releases/        reviewed Unity-ready export packages only
Legacy/Unreal/   historical .uasset/.umap reference; not Unity-importable
docs/            pipeline, migration manifest and release checklist
```

Read [the migration manifest](docs/MIGRATION_MANIFEST.md) before the initial import. The source tree is intentionally independent of Unity: Unity consumes reviewed copies from `Releases/`, never a live linked folder.
