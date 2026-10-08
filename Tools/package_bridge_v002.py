"""Publish the locally reviewed v002 candidate; never overwrite a release."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Source/Architecture/Bridge_Stone_A/v002"
TARGET = ROOT / "Releases/Bridge_Stone_A/v002"


def load_contract(path):
    spec = importlib.util.spec_from_file_location("fixed_bridge_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate()
    return module.contract()


def main():
    assert not TARGET.exists(), "Release already exists; never overwrite reviewed files."
    qa_path = SOURCE / "QA/roundtrip_report.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    assert qa["passed"]
    assert qa_path.stat().st_mtime >= (SOURCE / "QA/geometry_report.json").stat().st_mtime
    contract = load_contract(SOURCE / "bridge_contract.py")
    assert contract == json.loads((SOURCE / "bridge-site.json").read_text(encoding="utf-8"))
    TARGET.mkdir(parents=True)
    for folder in ("Meshes", "Textures", "QA", "Preview"):
        shutil.copytree(SOURCE / folder, TARGET / folder)
    for name in ("README.md", "bridge-site.json", "bridge_contract.py"):
        shutil.copy2(SOURCE / name, TARGET / name)
    assert load_contract(TARGET / "bridge_contract.py") == contract
    files = {
        path.relative_to(TARGET).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(TARGET.rglob("*")) if path.is_file()
    }
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    manifest = dict(
        asset_id="ENV_Bridge_Stone_A", version="v002", date="2026-10-08",
        status="Source/FBX reviewed candidate; Unity visual integration pending",
        unity_tested=False, generator_contract_tested=True,
        source="Source/Architecture/Bridge_Stone_A/v002/Bridge_Stone_A.blend",
        source_commit=head.stdout.strip() if head.returncode == 0 else None,
        source_uncommitted=True,
        source_sha256=hashlib.sha256((SOURCE / "Bridge_Stone_A.blend").read_bytes()).hexdigest(),
        blender_version="4.4.3", units="metres", axes="Y-up; road Z; river X",
        pivot="Crossing centre; approach grade Y=0", scale=[1, 1, 1],
        bridge_lod_triangles=[qa[f"bridge_lod{i}_triangles"] for i in range(3)],
        dressing_lod_triangles=[qa[f"dressing_lod{i}_triangles"] for i in range(3)],
        collider_intent="286 triangles; static non-convex, near gameplay only",
        textures=[key for key in files if key.startswith("Textures/")],
        preview="Preview/Bridge_Hero.png", files_sha256=files,
        integration_limits="Register reviewed prefab; connect global water and sockets; reroute rejected roads; enforce minimum crossings."
    )
    (TARGET / "release.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    for relative, expected in files.items():
        assert hashlib.sha256((TARGET / relative).read_bytes()).hexdigest() == expected
    print("BRIDGE_V002_PACKAGE_VERIFIED", TARGET, len(files), "files")


if __name__ == "__main__":
    main()
