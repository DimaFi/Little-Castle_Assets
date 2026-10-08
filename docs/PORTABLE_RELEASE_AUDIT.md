# Portable Source/Release audit — GPT-6 handoff (2026-10-08)

**Issue:** [Little-Castle_Assets #1](https://github.com/DimaFi/Little-Castle_Assets/issues/1)  
**Executor:** GPT-6 ChatGPT, explicitly assigned the previous Sol 6 / High queue by the user.  
**Base:** `DimaFi/Little-Castle_Assets/main` at `0e23f677e940ffdb8620abdd381f5bb1b23b0f9e`.  
**Status:** Portable-checkout analysis in progress; **actual complete hydrated checkout NOT VERIFIED** in this environment.

## Repository evidence inspected

Four distinct release manifests, without modifying released files:

| Release | Manifest schema | Manifest entries |
|---|---|---:|
| `Releases/Bridge_Stone_A/v001` | `files_sha256` map | 27 |
| `Releases/Bridge_Stone_A/v002` | `files_sha256` map | 31 |
| `Releases/Wall_Stone_Modular/v005` | `files` objects (`path`,`sha256`,`bytes`) | 26 |
| `Releases/TerrainStarter-v001` | historical `files` objects (`source`,`target`,`sha256`,`bytes`) | 16 |

`AssetBook/AssetBook.json`: 23 new versioned records; `AssetsDatabase/AssetBook.json` is a distinct legacy catalog. Neither catalog was rewritten. The connected GitHub tree at art commit `0e23f677` independently contains **278 versioned binary paths (197 Source, 81 Releases)**. The original handoff reports 172 unique LFS objects (~392 MB); **unique object/OID counts and hashes were not independently confirmed by a freshly hydrated checkout here**.

Some legacy TerrainStarter manifest entries contain Windows paths. Verifier should extract only the relative suffix after `Releases/TerrainStarter-v001/` and never use the historical machine-specific absolute path. The v002 bridge source imports v001 and versioned wall geometry through source-relative paths.

## New verification tasks

The portable-release verifier must validate committed Git LFS pointers against checkout payload hashes/sizes, PNG dimensions and FBX/Blend signatures, all four release manifest formats, raw text bytes (CRLF/LF), material-binding and FBX QA texture references, 23 separate versioned catalog IDs and stable dependencies, and portable bridge recipe imports. A missing LFS payload **must fail** with an actionable message. A metadata-only result cannot establish that art is portable.

The source tool and its synthetic-fixture offline unit tests may run without Blender/Unity. **Actual Blender texture packing, FBX import, Unity materials and visual acceptance cannot be certified without those applications.**

## Actual verification in ChatGPT environment

A local candidate verifier was compiled with Python and its synthetic offline suite passed **9/9 tests**. These checked manifest normalization, missing/corrupt payloads, pointer hydration, exact text bytes, image dimensions, path traversal, material dependencies and recipe-drive paths. This is **not** a run against the full published binary art checkout.

A direct attempt to clone GitHub in the execution container failed with `Could not resolve host: github.com`. Repository manifests and source text were inspected through the connected GitHub integration. **Full SHA-256 verification for all 392 MB of published LFS objects remains pending.**

## Required Codex/PC gate

Use a fresh checkout with working Git LFS and a normal network connection rather than an existing folder with local ignored art:

```powershell
git clone https://github.com/DimaFi/Little-Castle_Assets.git Little-Castle_Assets_portability_test
cd Little-Castle_Assets_portability_test
git lfs install
git lfs pull
python Tools/verify_portable_releases.py --json
python -m unittest discover -s Tools -p 'test_portable_releases.py' -v
python Tools/sync_asset_book.py
python Scripts/asset_book.py validate-catalog
```

Then Blender 4.4.3: reopen the source bridge v002 `.blend`, validate packed textures/material links, run published roundtrip/build check and inspect authored LOD0/1/2 FBX. Do not alter reviewed `Releases/**` in place. To fix assets, create a new version. Only then approve bridge art for [Unity import issue #9](https://github.com/DimaFi/Little-Castle/issues/9); Unity visual acceptance and GPU profiling are independent pending steps.

## Codex handoff

Preserve the current 23-record versioned AssetBook and the separate legacy AssetDatabase catalog; do not migrate their IDs. Read this report, art Issue #1 and linked PR before editing overlapping work. Published binary source/release files, `bridge_contract.py`, original wall/bridge geometry and both catalogs are immutable for this task. Source checks do not authorize altering them.
