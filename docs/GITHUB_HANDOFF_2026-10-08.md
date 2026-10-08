# User-authorized GitHub publication — 2026-10-08

The user requested: create GitHub tasks for Sol 6 / High, commit and upload all
current work, then continue from a phone in Chat and later from desktop Codex.
This explicitly overrides the old no-binary-publication policy only for the
current versioned `Source/` and `Releases/` work. The existing remote
`8428c45` legacy-workspace adoption commit has been preserved by fast-forward.

## Published scope

- `Source/`: existing local wall-kit versions, church versions, bridge v001/v002,
  their editable Blender files, FBX, materials, reference images, QA and scripts.
- `Releases/`: existing reviewed versioned wall and bridge packages.
- `AssetBook/`: 23-record versioned-work catalog, stable IDs preserved.
- `Tools/`: catalog maintenance and release packaging.
- Binary source/release files use Git LFS, not ordinary Git blobs. Approximately
  520 MiB existed before LFS deduplication; actual transfer differs.

The old `Art/`, `Mat/`, `AssetsDatabase/`, `Scripts/`, `Content/` and `Config/`
roots are preserved. Their historical local binary library has not been
remigrated or published. `AssetsDatabase/AssetBook.json` is the legacy catalog;
`AssetBook/AssetBook.json` describes the newer versioned work. Do not silently
merge, rename or replace IDs between them.

Engine caches, transient logs, `.blend1`/recovery files and Python bytecode stay
local. Unity `.meta` files do not belong in this source repository. Source
models are not automatically approved for production Unity catalog integration.

## Fresh checkout

```sh
git clone https://github.com/DimaFi/Little-Castle_Assets.git
cd Little-Castle_Assets
git lfs install
git lfs pull
python Tools/sync_asset_book.py
```

If Git LFS is unavailable, Blender/FBX/PNG files are text pointers, not the
actual models/images. Do not regenerate assets or report visual approval from
pointers. A cloud checkout does not imply Blender or licensed Unity is installed.

Bridge v002: `Source/Architecture/Bridge_Stone_A/v002` and
`Releases/Bridge_Stone_A/v002`. Fixed asset ID `ENV_Bridge_Stone_A`; 10.8 m length,
2.86 m clear path, local road +Z / river +X, scale 1, right-hand entrance flags.
The asset passed source/FBX checks, not Unity in-game visual acceptance.

The game continuation queue is in `DimaFi/Little-Castle` GitHub Issues and
`docs/handoffs/sol6-high-mobile-2026-10-08.md` on `current-unity-fix`.
