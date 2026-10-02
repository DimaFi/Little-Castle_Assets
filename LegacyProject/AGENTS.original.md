# Asset Book protocol

`AssetsDatabase/AssetBook.json` is the mandatory source of truth for every new art asset. `AssetBook.md` is generated output.

Before creating or exporting any model, material, texture, decal, foliage or modular part:

1. Run `python Scripts/asset_book.py search <synonyms, purpose, style, material>` from this project root.
2. Inspect the returned assets and their source files. For any sizeable request, state an `ASSET REUSE CHECK`: what is reused, what is genuinely missing, and why an existing near-match cannot be used.
3. If at least 70% can be assembled from the catalogue, create only the unique remainder.

Immediately after creating a new final asset, register it in the same task. Do not manually edit the generated Markdown:

```powershell
python Scripts/asset_book.py register Art/Props/Bench_B.fbx --id PROP_Bench_B --category Prop --subcategory Furniture --tag medieval --tag wood
```

Use the stable prefixes `BLD_`, `PROP_`, `VEG_`, `MOD_`, `MAT_`, and `TEX_`. Then run `python Scripts/asset_book.py sync`. A task that creates an asset is incomplete until the register command succeeds. If the created item is a composite, record its dependencies and `used_by` links in `AssetBook.json` before the sync.

Never create a variant merely because a task names it differently. A new variant must document the concrete incompatibility (scale, style, function, or technical requirement) in its Asset Book notes.
