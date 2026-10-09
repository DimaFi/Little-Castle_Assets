"""Read-only portability audit for Little Castle versioned art packages.

Full check (requires hydrated LFS):
    python Tools/verify_portable_releases.py
Metadata mode is NOT a portability PASS:
    python Tools/verify_portable_releases.py --metadata-only
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LFS_EXTENSIONS = {".blend", ".fbx", ".png", ".jpg", ".jpeg", ".exr", ".tga", ".psd"}
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
POINTER = re.compile(rb"\Aversion https://git-lfs.github.com/spec/v1\r?\noid sha256:([a-f0-9]{64})\r?\nsize ([0-9]+)\r?\n\Z")


class AuditError(ValueError):
    """Missing, corrupted or non-portable source/release input."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def safe_path(root: Path, relative: str) -> Path:
    require(isinstance(relative, str) and relative != "", "Missing relative file path")
    require("\\" not in relative and ":" not in relative, f"Non-portable path: {relative}")
    parts = PurePosixPath(relative).parts
    require(relative[0] != "/" and ".." not in parts, f"Escaping path: {relative}")
    require(all(part not in ("", ".") for part in parts), f"Bad path: {relative}")
    return root.joinpath(*parts)


def lfs_pointer(data: bytes) -> tuple[str, int] | None:
    if not data.startswith(b"version https://git-lfs.github.com/spec/v1"):
        return None
    match = POINTER.fullmatch(data)
    require(match is not None, "Malformed Git LFS pointer")
    return match.group(1).decode("ascii"), int(match.group(2))


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(repo: Path, relpath: str) -> bytes:
    run = subprocess.run(
        ["git", "-C", str(repo), "show", "HEAD:" + relpath],
        capture_output=True, check=False,
    )
    require(run.returncode == 0, f"Missing committed Git blob {relpath}: {run.stderr.decode(errors='replace')[:200]}")
    return run.stdout


def tracked_files(repo: Path) -> list[str]:
    run = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z"],
        capture_output=True, check=False,
    )
    require(run.returncode == 0, "Cannot list tracked Git files; use a Git checkout")
    return [x.decode("utf-8") for x in run.stdout.split(b"\0") if x]


def check_signature(path: str, data: bytes) -> dict[str, Any]:
    """Lightweight file-type sanity, not a Blender/Unity visual validation."""
    ext = Path(path).suffix.lower()
    if ext == ".png":
        require(len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n", f"Not a PNG: {path}")
        require(data[12:16] == b"IHDR", f"PNG IHDR missing: {path}")
        width, height = struct.unpack(">II", data[16:24])
        require(0 < width <= 32768 and 0 < height <= 32768, f"Invalid PNG dimensions: {path}")
        return {"width": width, "height": height}
    if ext == ".blend":
        require(data.startswith(b"BLENDER") and len(data) >= 12, f"Not a Blender file: {path}")
    if ext == ".fbx":
        require(data.startswith(b"Kaydara FBX Binary  \x00\x1a\x00") or data.lstrip().startswith(b"; FBX"), f"Not an FBX: {path}")
    if ext in (".jpg", ".jpeg"):
        require(data[:3] == b"\xff\xd8\xff", f"Not a JPEG: {path}")
    return {}


def release_entries(manifest: dict[str, Any], release_name: str) -> list[tuple[str, str, int | None]]:
    """Normalize bridge, walls and historical TerrainStarter manifests."""
    if isinstance(manifest.get("files_sha256"), dict):
        raw = [(p, digest, None) for p, digest in manifest["files_sha256"].items()]
    elif isinstance(manifest.get("files"), list):
        raw = []
        for item in manifest["files"]:
            require(isinstance(item, dict), "Expected release files list of objects")
            rel = item.get("path")
            if rel is None:
                source = str(item.get("source", "")).replace("\\", "/")
                marker = "/Releases/" + release_name + "/"
                if source.startswith("Releases/" + release_name + "/"):
                    rel = source[len("Releases/" + release_name + "/"):]
                else:
                    require(marker in source, f"Cannot resolve legacy source relative to release: {source}")
                    rel = source.rsplit(marker, 1)[1]
            raw.append((rel, item.get("sha256"), item.get("bytes")))
    else:
        raise AuditError("Unknown manifest format (expected files_sha256 or files)")
    require(len(raw) > 0, "Empty release manifest")
    names = [x[0] for x in raw]
    require(len(names) == len(set(names)), "Duplicate path in release manifest")
    for name, digest, count in raw:
        safe_path(Path("."), name)
        require(isinstance(digest, str) and HEX64.fullmatch(digest) is not None, f"Bad SHA-256: {name}")
        require(count is None or isinstance(count, int) and count >= 0, f"Bad byte count: {name}")
    return raw


def validate_texture_dependencies(release: Path, files: set[str]) -> dict[str, int]:
    """Check material binding and FBX QA texture references, not .blend image packing."""
    result = {"material_bindings": 0, "qa_texture_references": 0}

    def texture_path(reference: str) -> str:
        require(isinstance(reference, str) and reference, f"{release.name}: bad texture reference")
        normalized = reference.replace("\\", "/")
        require(not normalized.startswith("/") and ":" not in normalized,
                f"{release.name}: non-portable texture reference: {reference}")
        parts: list[str] = []
        for part in normalized.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                require(bool(parts), f"{release.name}: escaping texture reference: {reference}")
                parts.pop()
            else:
                parts.append(part)
        if len(parts) == 1:
            parts.insert(0, "Textures")
        require(len(parts) == 2 and parts[0] == "Textures",
                f"{release.name}: invalid texture reference: {reference}")
        return "/".join(parts)

    binding_rel = "Textures/material-bindings.json"
    if binding_rel in files:
        binding = json.loads((release / binding_rel).read_text(encoding="utf-8"))
        materials = binding.get("materials", {})
        require(isinstance(materials, dict), "Bad material bindings")
        for material, values in materials.items():
            if not isinstance(values, dict):
                continue
            main = values.get("_MainTex")
            if main:
                require(texture_path(main) in files, f"{release.name}: missing texture dependency for {material}: {main}")
                result["material_bindings"] += 1
    report_rel = "QA/roundtrip_report.json"
    if report_rel in files:
        report = json.loads((release / report_rel).read_text(encoding="utf-8"))
        require(report.get("passed") is True, f"{release.name}: FBX QA reported failure")
        for objects in report.get("files", {}).values():
            for object_info in objects:
                for texture in object_info.get("textures", []):
                    require(texture_path(texture) in files, f"{release.name}: QA references missing texture: {texture}")
                    result["qa_texture_references"] += 1
    return result


def audit_release(repo: Path, manifest_path: Path, *, metadata_only: bool = False, compare_git: bool = True) -> dict[str, Any]:
    release = manifest_path.parent
    rel = release.relative_to(repo).as_posix()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    items = release_entries(manifest, release.name)
    result = {"release": rel, "files": len(items), "bytes": 0, "dimensions": {}, "status": "METADATA_ONLY" if metadata_only else "PASS"}
    expected_files = {name for name, _, _ in items}
    if not metadata_only:
        for path, expected_sha, expected_size in items:
            target = safe_path(release, path)
            require(target.is_file(), f"{rel}/{path}: missing; check checkout and git lfs pull")
            data = target.read_bytes()
            pointer = lfs_pointer(data)
            require(pointer is None, f"{rel}/{path}: Git LFS pointer instead of payload; run git lfs pull")
            require(sha256(data) == expected_sha, f"{rel}/{path}: SHA-256 mismatch")
            if expected_size is not None:
                require(len(data) == expected_size, f"{rel}/{path}: size mismatch")
            result["bytes"] += len(data)
            dimensions = check_signature(path, data)
            if dimensions:
                result["dimensions"][path] = dimensions
            if compare_git and Path(path).suffix.lower() not in LFS_EXTENSIONS:
                committed = git_blob(repo, f"{rel}/{path}")
                require(data == committed, f"{rel}/{path}: checkout changed exact committed bytes (CRLF/LF?)")
        for path in manifest.get("textures", []):
            require(path in expected_files, f"{rel}: texture not included in manifest: {path}")
        for key in ("preview", "geometry_report"):
            value = manifest.get(key)
            if value:
                require(value in expected_files, f"{rel}: {key} absent from manifest: {value}")
        result["dependencies"] = validate_texture_dependencies(release, expected_files)
        if manifest.get("source_sha256"):
            source = manifest.get("source")
            if source and str(source).endswith(".blend") and not Path(str(source)).is_absolute():
                original = safe_path(repo, source)
                require(original.is_file(), f"{rel}: source blend missing: {source}")
                data = original.read_bytes()
                require(lfs_pointer(data) is None, f"{rel}: source is LFS pointer; run git lfs pull")
                require(sha256(data) == manifest["source_sha256"], f"{rel}: source SHA-256 differs")
    return result


def audit_lfs(repo: Path, tracked: list[str], *, metadata_only: bool = False) -> dict[str, Any]:
    paths = [p for p in tracked if p.startswith(("Source/", "Releases/")) and Path(p).suffix.lower() in LFS_EXTENSIONS]
    unique: dict[str, int] = {}
    missing = []
    for path in paths:
        oid_size = lfs_pointer(git_blob(repo, path))
        require(oid_size is not None, f"{path}: binary Git blob not stored as LFS pointer")
        oid, size = oid_size
        unique[oid] = size
        if metadata_only:
            continue
        target = safe_path(repo, path)
        if not target.is_file():
            missing.append(f"{path}: absent; run git lfs pull")
            continue
        data = target.read_bytes()
        if lfs_pointer(data) is not None:
            missing.append(f"{path}: pointer not hydrated; run git lfs pull")
            continue
        require(len(data) == size and sha256(data) == oid, f"{path}: LFS content differs from committed OID/size")
        check_signature(path, data)
    require(not missing, f"{len(missing)} LFS payload(s) unavailable, e.g. " + "; ".join(missing[:3]))
    return {"tracked_lfs_paths": len(paths), "unique_lfs_objects": len(unique), "unique_bytes": sum(unique.values())}


def audit_asset_book(repo: Path, *, metadata_only: bool = False) -> dict[str, Any]:
    book = json.loads((repo / "AssetBook/AssetBook.json").read_text(encoding="utf-8"))
    records = book["assets"]
    names = [x["id"] for x in records]
    require(len(names) == len(set(names)), "Duplicate new AssetBook IDs")
    # The 2026-10-08 handoff had 23 records. Preserve that baseline while allowing
    # the explicitly versioned CliffKit intake, whose files are audited below too.
    cliff_names = {"ENV_CliffKit_" + name for name in (
        "Cliff_Straight_A", "Cliff_Straight_B", "Cliff_Convex_A", "Cliff_Concave_A",
        "Cliff_Terrace_Low", "Cliff_Terrace_High", "Cliff_End_Left", "Cliff_End_Right",
        "Rock_Outcrop_Large", "Rock_Outcrop_Medium", "Rock_Boulder_Small", "Rock_Boulder_Large",
        "Ramp_Hike_A", "Ramp_Hike_B")}
    present_cliffs = set(names) & cliff_names
    require(not present_cliffs or present_cliffs == cliff_names, "Incomplete CliffKit catalog intake")
    require(len(records) == 23 + len(present_cliffs),
            f"Expected preserved 23 records plus optional complete 14-record CliffKit, got {len(records)}")
    require((repo / "AssetsDatabase/AssetBook.json").is_file(), "Legacy AssetsDatabase catalog missing")
    for record in records:
        for dependency in record.get("dependencies", []):
            require(dependency in names, f"Unresolved {record['id']} dependency: {dependency}")
        paths = [str(PurePosixPath(record["path"]) / record["source_file"])]
        if record.get("editable_source"):
            paths.append(record["editable_source"])
        for p in paths:
            target = safe_path(repo, p)
            require(target.is_file(), f"AssetBook {record['id']}: missing {p}")
            if not metadata_only:
                require(lfs_pointer(target.read_bytes()) is None, f"AssetBook {record['id']}: LFS pointer {p}")
    return {"versioned_records": len(records), "legacy_catalog_preserved": True}


def audit_bridge_recipe(repo: Path) -> dict[str, Any]:
    base = repo / "Source/Architecture/Bridge_Stone_A/v002"
    dependencies = [
        base / "build_bridge.py", base / "validate_bridge.py",
        base / "bridge_contract.py", base / "bridge-site.json",
        base.parent / "v001/build_bridge.py",
        repo / "Source/Architecture/Wall_Stone_Modular/v005/wall_geometry.py",
        repo / "Source/Dependencies/Bridge_Stone_A/SM_Grass_Short_A.fbx",
    ]
    for path in dependencies:
        require(path.is_file(), f"Bridge v002 source dependency absent: {path.relative_to(repo)}")
    for path in dependencies:
        if path.suffix != ".py":
            continue
        text = path.read_text(encoding="utf-8")
        require(not re.search(r"[A-Za-z]:[\\/]", text), f"Absolute Windows drive path in bridge recipe: {path.relative_to(repo)}")
        require(not re.search(r"(?:/Users/|/home/[^/]+/Downloads/)", text), f"User-specific path in bridge recipe: {path.relative_to(repo)}")
    contract = json.loads((base / "bridge-site.json").read_text(encoding="utf-8"))
    require(contract["asset_id"] == "ENV_Bridge_Stone_A" and contract["version"] == "v002", "Bridge recipe asset ID/version changed")
    require(contract["bridge_length"] == 10.8 and contract["clear_walk_width"] == 2.86, "Fixed bridge size changed")
    return {"bridge_recipe_dependencies": len(dependencies), "fixed_bridge_contract": "10.8m / 2.86m"}


def run(repo: Path, *, metadata_only: bool = False) -> dict[str, Any]:
    repo = repo.resolve()
    tracked = tracked_files(repo)
    paths = sorted(repo.glob("Releases/**/release.json"))
    require(len(paths) >= 4, f"Expected >=4 versioned release manifests; got {len(paths)}")
    reports = [audit_release(repo, p, metadata_only=metadata_only) for p in paths]
    return {
        "mode": "METADATA_ONLY_NOT_A_PASS" if metadata_only else "FULL_LOCAL_VERIFICATION",
        "releases": reports,
        "lfs": audit_lfs(repo, tracked, metadata_only=metadata_only),
        "asset_book": audit_asset_book(repo, metadata_only=metadata_only),
        "bridge_recipe": audit_bridge_recipe(repo),
        "unity_visual_approval": False,
        "blender_rebuild_verified": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--metadata-only", action="store_true", help="Inspect manifests/Git pointers only; does not verify payloads")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = run(args.repo, metadata_only=args.metadata_only)
    except (AuditError, ValueError, OSError, subprocess.SubprocessError) as exc:
        print("PORTABLE_AUDIT_FAILED:", str(exc), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("PORTABLE_AUDIT_" + ("METADATA_ONLY" if args.metadata_only else "PASS"))
        for release in result["releases"]:
            print(" -", release["release"], release["files"], "files", release["status"])
        print("LFS", result["lfs"])
        print("AssetBook", result["asset_book"])
        print("Unity and Blender visual/rebuild approvals: NOT TESTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
