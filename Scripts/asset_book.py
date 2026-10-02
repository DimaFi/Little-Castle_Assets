#!/usr/bin/env python3
"""Asset Book maintenance for CozySettlement.

Run from the project root:
  python Scripts/asset_book.py bootstrap  # first-time catalogue creation
  python Scripts/asset_book.py sync       # check files and refresh AssetBook.md
  python Scripts/asset_book.py search mill door roof
  python Scripts/asset_book.py register Art/Props/New_Bench.fbx --id PROP_Bench_B --category Prop
  python Scripts/asset_book.py validate

The JSON file is the source of truth.  `sync` never invents an asset record:
it reports models found on disk but absent from the Book, so a human can give
them a useful ID, category and reuse information via `register`.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_DIR = ROOT / "AssetsDatabase"
BOOK_PATH = DB_DIR / "AssetBook.json"
SUMMARY_PATH = DB_DIR / "AssetBook.md"
EXCLUDED_PARTS = {"Saved", "Intermediate", "DerivedDataCache", "Binaries", "Build", "Renders", "References", "QA"}
ASSET_EXTENSIONS = {".fbx", ".blend", ".uasset"}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def words(value: str) -> list[str]:
    return [word.lower() for word in re.split(r"[^A-Za-z0-9А-Яа-я]+", value) if word]


def title_from_stem(stem: str) -> str:
    return re.sub(r"[_-]+", " ", stem).replace("SM ", "").strip()


def prefix_for(category: str) -> str:
    return {"Building": "BLD", "Prop": "PROP", "Vegetation": "VEG", "Material": "MAT", "Texture": "TEX", "Modular Component": "MOD"}[category]


def make_asset(asset_id: str, name: str, category: str, subcategory: str, path: str, source_file: str,
               tags: list[str], *, status: str = "Ready", lods: list[str] | None = None,
               materials: list[str] | None = None, textures: list[str] | None = None,
               dependencies: list[str] | None = None, reusable_parts: list[str] | None = None,
               related_assets: list[str] | None = None, notes: str = "") -> dict:
    return {
        "id": asset_id, "name": name, "category": category, "subcategory": subcategory,
        "status": status, "path": path, "source_file": source_file, "tags": sorted(set(tags)),
        "reusable_parts": reusable_parts or [], "materials": materials or [], "textures": textures or [],
        "lods": lods or [], "dependencies": dependencies or [], "related_assets": related_assets or [],
        "used_by": [], "can_reuse": status == "Ready", "notes": notes,
    }


def make_material_assets() -> list[dict]:
    suites: list[tuple[str, Path, list[str]]] = []
    mat = ROOT / "Mat"
    for folder in [mat / "Bark", mat / "DoorWood", mat / "Logs_Bark", mat / "RoofTile", mat / "Shutters",
                   mat / "T_ChimneyStone", mat / "T_FieldStone", mat / "T_Foliage", mat / "T_Plaster",
                   mat / "T_Timber", mat / "Tree02_Bark", mat / "Tree02_Leaves", mat / "Tree02_Moss", mat / "Tree02_Rocks"]:
        if folder.is_dir():
            suites.append((folder.name, folder, words(folder.name)))
    terrain = mat / "Material_terrain"
    if terrain.is_dir():
        for folder in terrain.rglob("*"):
            if folder.is_dir() and any(file.suffix.lower() in {".png", ".jpg", ".exr"} for file in folder.iterdir()):
                suites.append((folder.name, folder, words(folder.name) + words(folder.parent.name)))
    assets = []
    for suite_name, folder, tags in suites:
        clean = re.sub(r"[^A-Za-z0-9]+", "_", suite_name).strip("_")
        tex_id = f"TEX_{clean}"
        material_id = f"MAT_{clean}"
        files = sorted(file.name for file in folder.iterdir() if file.is_file() and file.suffix.lower() in {".png", ".jpg", ".exr"})
        source = next((name for name in files if "BaseColor" in name or "Albedo" in name), files[0])
        assets.append(make_asset(tex_id, f"{title_from_stem(suite_name)} texture set", "Texture", "PBR texture set", rel(folder), source,
                                 tags + ["pbr", "texture"], notes="Source map suite; contains the maps listed in its folder."))
        assets.append(make_asset(material_id, title_from_stem(suite_name), "Material", "Surface material", rel(folder), source,
                                 tags + ["material", "pbr"], textures=[tex_id], dependencies=[tex_id],
                                 notes="Material specification based on the registered texture set."))
    return assets


def bootstrap() -> dict:
    assets: list[dict] = []
    # Current, documented cottage modules take precedence over older work-in-progress versions.
    catalog = ROOT / "Art/House_Cottage_A/Docs/07_Module_Catalog_RU.md"
    module_paths: dict[str, Path] = {}
    if catalog.exists():
        for match in re.finditer(r"\]\((\.\./Source/[^)]+\.blend)\)", catalog.read_text(encoding="utf-8")):
            path = (catalog.parent / match.group(1)).resolve()
            module_paths[path.stem] = path
    for stem, source in sorted(module_paths.items()):
        subcategory = "Architecture"
        category = "Modular Component" if any(key in stem for key in ("Door", "Window", "Timber", "Fence", "Gate", "StoneWall")) else "Prop"
        asset_id = f"{prefix_for(category)}_{stem.removeprefix('SM_')}"
        assets.append(make_asset(asset_id, title_from_stem(stem), category, subcategory, rel(source.parent), source.name,
                                 words(stem) + ["medieval", "cottage", "reusable"],
                                 notes="Latest documented standalone cottage module."))

    module_ids = [asset["id"] for asset in assets]
    house_source = ROOT / "Art/House_Cottage_A/Source/Roof/v018/House_Cottage_A.blend"
    assets.append(make_asset("BLD_House_Cottage_A", "Cottage House A", "Building", "Cottage", rel(house_source.parent), house_source.name,
                             ["medieval", "cottage", "house", "timber", "plaster", "stone", "residential"],
                             dependencies=module_ids, reusable_parts=module_ids,
                             notes="Current house assembly source; individual architectural and yard parts are registered separately."))

    # Exported oak kit: every file is reusable except LOD files, which belong to the hero tree.
    oak = ROOT / "Art/Vegetation/Oak_Kit/Exports"
    for file in sorted(oak.glob("*.fbx")):
        stem = file.stem
        if stem.endswith("_LOD1") or stem.endswith("_LOD2"):
            continue
        lods = ["LOD0", "LOD1", "LOD2"] if stem == "SM_Tree_Oak_A" else []
        assets.append(make_asset(f"VEG_{stem.removeprefix('SM_')}", title_from_stem(stem), "Vegetation", "Oak kit", rel(file.parent), file.name,
                                 words(stem) + ["oak", "stylized", "reusable"], lods=lods,
                                 materials=["MAT_Bark", "MAT_T_Foliage"] if stem == "SM_Tree_Oak_A" else [],
                                 notes="Exported reusable oak-kit mesh."))

    # Other final FBX exports.  Historical/reference exports are deliberately not catalogued as game assets.
    known_fbx = [
        ("BLD_Cottage_01", "Cottage 01", "Building", "Cottage", "Art/Cottage/Cottage_01.fbx", [], []),
        ("BLD_Cottage_02", "Cottage 02", "Building", "Cottage", "Art/Cottage/Cottage_02.fbx", [], []),
        ("BLD_Cottage_03", "Cottage 03", "Building", "Cottage", "Art/Cottage/Cottage_03.fbx", [], []),
        ("PROP_Birdhouse_01", "Birdhouse 01", "Prop", "Birdhouse", "Art/Props/Birdhouse_01.fbx", [], []),
        ("PROP_Lantern_01", "Lantern 01", "Prop", "Lantern", "Art/Props/Lantern_01.fbx", [], []),
        ("VEG_Tree_01", "Tree 01", "Vegetation", "Tree", "Art/Vegetation/Tree_01/Tree_01.fbx", [], []),
        ("VEG_Tree_02", "Tree 02", "Vegetation", "Tree", "Art/Vegetation/Tree_01/Tree_02_LOD0.fbx", ["LOD0", "LOD1", "LOD2"], []),
        ("VEG_Tree_03", "Tree 03", "Vegetation", "Tree", "Art/Vegetation/Tree_01/Tree_03/Tree_03_LOD0.fbx", ["LOD0", "LOD1", "LOD2"], ["PROP_Birdhouse_01", "PROP_Lantern_01"]),
        ("VEG_Tree_04", "Tree 04", "Vegetation", "Tree", "Art/Vegetation/Tree_01/Tree_04/Tree_04_LOD0.fbx", ["LOD0", "LOD1", "LOD2"], ["PROP_Birdhouse_01", "PROP_Lantern_01"]),
    ]
    for asset_id, name, category, subcategory, source_rel, lods, deps in known_fbx:
        source = ROOT / source_rel
        assets.append(make_asset(asset_id, name, category, subcategory, rel(source.parent), source.name,
                                 words(name) + ["stylized", "reusable"], lods=lods, dependencies=deps))

    assets.extend(make_material_assets())
    # Materials imported into Unreal are useful for search even where their source maps are elsewhere.
    for file in sorted((ROOT / "Content/Art/Cottage").glob("*.uasset")):
        stem = re.sub(r"[^A-Za-z0-9]+", "_", file.stem).strip("_")
        assets.append(make_asset(f"MAT_UE_{stem}", title_from_stem(file.stem), "Material", "Unreal material", rel(file.parent), file.name,
                                 words(file.stem) + ["unreal", "cottage", "material"], notes="Imported Unreal asset; inspect in Unreal before editing."))

    book = {
        "schema_version": "1.0",
        "project": "CozySettlement",
        "updated": date.today().isoformat(),
        "rules": {
            "required_statuses": ["Planned", "InProgress", "NeedsFix", "Ready", "Deprecated", "Missing"],
            "reuse_threshold_percent": 70,
            "workflow": "Before modelling: search Asset Book, inspect candidate files, publish an Asset Reuse Check, then create only missing parts. Register every completed asset before closing the task."
        },
        "assets": assets,
    }
    rebuild_used_by(book)
    return book


def rebuild_used_by(book: dict) -> None:
    by_id = {asset["id"]: asset for asset in book["assets"]}
    for asset in book["assets"]:
        asset["used_by"] = []
    for asset in book["assets"]:
        for dependency in asset.get("dependencies", []):
            if dependency in by_id:
                by_id[dependency]["used_by"].append(asset["id"])
    for asset in book["assets"]:
        asset["used_by"].sort()


def rebuild_search_index(book: dict) -> None:
    """Store a normalized reverse index, so lookup needs no filesystem scan."""
    index: dict[str, list[str]] = defaultdict(list)
    for asset in book["assets"]:
        searchable = " ".join([
            asset["id"], asset["name"], asset["category"], asset["subcategory"],
            *asset.get("tags", []), *asset.get("reusable_parts", []), asset.get("notes", ""),
        ])
        for token in set(words(searchable)):
            index[token].append(asset["id"])
    book["search_index"] = {token: sorted(ids) for token, ids in sorted(index.items())}


def save(book: dict) -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    book["updated"] = date.today().isoformat()
    rebuild_search_index(book)
    BOOK_PATH.write_text(json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render(book: dict) -> str:
    counts = Counter(asset["status"] for asset in book["assets"])
    lines = ["# Asset Book — CozySettlement", "", "Автоматически создано из `AssetBook.json`. Не редактируйте эту сводку вручную.", "",
             f"Обновлено: `{book['updated']}` · Всего записей: **{len(book['assets'])}**.", "",
             "## Обязательный процесс", "", "1. До моделирования выполните поиск по назначению, стилю, материалам и синонимам.", "2. Проверьте найденные файлы на диске и опубликуйте `ASSET REUSE CHECK`.", "3. Создавайте только отсутствующие или объективно неподходящие части.", "4. После работы зарегистрируйте ассет и запустите `python Scripts/asset_book.py sync`.", "",
             "## Сводка статусов", "", "| Статус | Количество |", "|---|---:|"]
    lines += [f"| {status} | {count} |" for status, count in sorted(counts.items())]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for asset in book["assets"]:
        grouped[asset["category"]].append(asset)
    for category in sorted(grouped):
        lines += ["", f"## {category}", "", "| ID | Название | Подкатегория | Статус | Файл |", "|---|---|---|---|---|"]
        for asset in sorted(grouped[category], key=lambda item: item["id"]):
            file_ref = f"[{asset['source_file']}](../{asset['path']}/{asset['source_file']})"
            lines.append(f"| `{asset['id']}` | {asset['name']} | {asset['subcategory']} | {asset['status']} | {file_ref} |")
    lines += ["", "## Формат проверки перед созданием", "", "```text", "ASSET REUSE CHECK", "Найдено и будет переиспользовано:", "✓ <asset ID>", "Необходимо создать:", "+ <new asset ID>", "Причина нового варианта: <почему существующие варианты не подходят>", "``", ""]
    return "\n".join(lines)


def load() -> dict:
    if not BOOK_PATH.exists():
        raise SystemExit("AssetBook.json отсутствует. Сначала запустите: python Scripts/asset_book.py bootstrap")
    return json.loads(BOOK_PATH.read_text(encoding="utf-8"))


def path_for(asset: dict) -> Path:
    return ROOT / asset["path"] / asset["source_file"]


def discoverable_models() -> set[str]:
    """Return final export candidates, excluding source history and LOD companions.

    A `.blend` is normally a working/source revision, not another game asset.  The
    final FBX is what needs an independent catalogue record.  LOD1/2 and the
    birdhouse/lantern files embedded in the tree exports are covered by their
    primary asset records and therefore must not produce duplicate warnings.
    """
    result = set()
    for path in ROOT.joinpath("Art").rglob("*"):
        if not path.is_file() or path.suffix.lower() != ".fbx":
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if "Reference" in path.name or re.search(r"_LOD[12]\.fbx$", path.name):
            continue
        if re.match(r"Tree0[34]_(Birdhouse|Lantern)_", path.stem):
            continue
        result.add(rel(path))
    return result


def validate(book: dict, quiet: bool = False, check_files: bool = True) -> int:
    errors: list[str] = []
    ids = [asset.get("id") for asset in book.get("assets", [])]
    if len(ids) != len(set(ids)):
        errors.append("duplicate asset IDs")
    known = set(ids)
    for asset in book["assets"]:
        if asset["status"] not in book["rules"]["required_statuses"]:
            errors.append(f"{asset['id']}: invalid status {asset['status']}")
        if check_files and not path_for(asset).exists() and asset["status"] != "Missing":
            errors.append(f"{asset['id']}: source file is missing ({path_for(asset)})")
        for reference in asset.get("dependencies", []) + asset.get("related_assets", []) + asset.get("materials", []) + asset.get("textures", []):
            if reference not in known:
                errors.append(f"{asset['id']}: unknown reference {reference}")
    registered_paths = {rel(path_for(asset)) for asset in book["assets"] if path_for(asset).exists()}
    unregistered = sorted(discoverable_models() - registered_paths) if check_files else []
    if not quiet:
        print(f"Asset Book: {len(book['assets'])} records, {len(errors)} errors, {len(unregistered)} unregistered candidate model files.")
        for error in errors:
            print("ERROR:", error)
        for path in unregistered:
            print("UNREGISTERED:", path)
    return 1 if errors else 0


def sync() -> int:
    book = load()
    for asset in book["assets"]:
        if not path_for(asset).exists() and asset["status"] != "Deprecated":
            asset["status"] = "Missing"
            asset["can_reuse"] = False
    rebuild_used_by(book)
    save(book)
    SUMMARY_PATH.write_text(render(book), encoding="utf-8")
    return validate(book)


def search(book: dict, query: list[str]) -> int:
    needles = set(words(" ".join(query)))
    by_id = {asset["id"]: asset for asset in book["assets"]}
    scores: Counter[str] = Counter()
    for needle in needles:
        for asset_id in book.get("search_index", {}).get(needle, []):
            scores[asset_id] += 1
    scored = [(score, by_id[asset_id]) for asset_id, score in scores.items()]
    for score, asset in sorted(scored, key=lambda pair: (-pair[0], pair[1]["id"])):
        print(f"[{score}] {asset['id']} | {asset['status']} | {asset['category']} | {asset['path']}/{asset['source_file']}")
    return 0 if scored else 1


def register(book: dict, args: argparse.Namespace) -> int:
    source = Path(args.path)
    if not source.is_absolute():
        source = ROOT / source
    source = source.resolve()
    if not source.is_file():
        raise SystemExit(f"Asset source not found: {source}")
    try:
        source_rel = rel(source)
    except ValueError as error:
        raise SystemExit("Asset source must be inside the CozySettlement project.") from error
    if any(asset["id"] == args.asset_id for asset in book["assets"]):
        raise SystemExit(f"Asset ID already exists: {args.asset_id}")
    if any(rel(path_for(asset)) == source_rel for asset in book["assets"]):
        raise SystemExit(f"This source file is already registered: {source_rel}")
    category = args.category
    if category not in {"Building", "Prop", "Vegetation", "Material", "Texture", "Modular Component"}:
        raise SystemExit("Unsupported category. Use Building, Prop, Vegetation, Material, Texture or Modular Component.")
    expected_prefix = prefix_for(category) + "_"
    if not args.asset_id.startswith(expected_prefix):
        raise SystemExit(f"ID for {category} must start with {expected_prefix}")
    name = args.name or title_from_stem(source.stem)
    tags = sorted(set(words(" ".join([args.asset_id, name, category, args.subcategory, *args.tags]))))
    book["assets"].append(make_asset(args.asset_id, name, category, args.subcategory, rel(source.parent), source.name, tags,
                                     status=args.status, notes=args.notes or "Registered on asset creation."))
    rebuild_used_by(book)
    save(book)
    SUMMARY_PATH.write_text(render(book), encoding="utf-8")
    print(f"REGISTERED: {args.asset_id} -> {source_rel}")
    return validate(book)


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain the CozySettlement Asset Book.")
    parser.add_argument("command", choices=["bootstrap", "sync", "validate", "validate-catalog", "search", "register"])
    parser.add_argument("query", nargs="*")
    parser.add_argument("--id", dest="asset_id", help="Stable Asset Book ID, e.g. PROP_Bench_B")
    parser.add_argument("--category", help="Asset category")
    parser.add_argument("--subcategory", default="Unclassified", help="Specific reuse group")
    parser.add_argument("--name", help="Human-readable name")
    parser.add_argument("--tag", dest="tags", action="append", default=[], help="Search tag; repeat as needed")
    parser.add_argument("--status", default="Ready", help="Planned, InProgress, NeedsFix, Ready, Deprecated or Missing")
    parser.add_argument("--notes", default="", help="Why this asset exists or how to reuse it")
    args = parser.parse_args()
    if args.command == "bootstrap":
        if BOOK_PATH.exists():
            raise SystemExit("AssetBook.json already exists; use sync or edit the registry intentionally.")
        book = bootstrap()
        save(book)
        SUMMARY_PATH.write_text(render(book), encoding="utf-8")
        return validate(book)
    book = load()
    if args.command == "register":
        if len(args.query) != 1 or not args.asset_id or not args.category:
            raise SystemExit("Usage: register <source-file> --id <ID> --category <category> [--subcategory <group>]")
        args.path = args.query[0]
        return register(book, args)
    if args.command == "sync":
        return sync()
    if args.command == "validate":
        return validate(book)
    if args.command == "validate-catalog":
        return validate(book, check_files=False)
    return search(book, args.query)


if __name__ == "__main__":
    sys.exit(main())
