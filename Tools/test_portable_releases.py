"""Offline unit tests for portable-release verifier; no Blender or Unity required.

Run: python -m unittest discover -s Tools -p 'test_portable_releases.py' -v
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("verify_portable_releases.py")
SPEC = importlib.util.spec_from_file_location("portable", SCRIPT)
portable = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(portable)


def png(width=3, height=4):
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", width, height) + bytes([8, 6, 0, 0, 0])


def save_json(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")


class PortableReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.release = self.repo / "Releases/Bridge_Stone_A/v002"
        (self.release / "Textures").mkdir(parents=True)
        self.texture = png()
        (self.release / "Textures/demo.png").write_bytes(self.texture)
        (self.release / "README.md").write_bytes(b"CRLF\r\nexample\r\n")
        self.manifest = self.release / "release.json"
        save_json(self.manifest, {
            "version": "v002", "asset_id": "ENV_Bridge_Stone_A",
            "textures": ["Textures/demo.png"],
            "files_sha256": {
                "Textures/demo.png": portable.sha256(self.texture),
                "README.md": portable.sha256((self.release / "README.md").read_bytes()),
            },
        })

    def tearDown(self):
        self.tmp.cleanup()

    def test_bridge_format_validates_bytes_dimensions_and_missing_tex(self):
        result = portable.audit_release(self.repo, self.manifest, compare_git=False)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["dimensions"]["Textures/demo.png"], {"width": 3, "height": 4})
        (self.release / "Textures/demo.png").unlink()
        with self.assertRaisesRegex(portable.AuditError, "missing"):
            portable.audit_release(self.repo, self.manifest, compare_git=False)

    def test_manifest_detects_corruption_and_lfs_pointer(self):
        target = self.release / "Textures/demo.png"
        target.write_bytes(self.texture + b"corrupted")
        with self.assertRaisesRegex(portable.AuditError, "SHA-256 mismatch"):
            portable.audit_release(self.repo, self.manifest, compare_git=False)
        target.write_bytes(b"version https://git-lfs.github.com/spec/v1\noid sha256:" + b"a" * 64 + b"\nsize 100\n")
        with self.assertRaisesRegex(portable.AuditError, "git lfs pull"):
            portable.audit_release(self.repo, self.manifest, compare_git=False)

    def test_wall_format_and_legacy_windows_path(self):
        entry = {"sha256": "a" * 64, "bytes": 123}
        self.assertEqual(
            portable.release_entries({"files": [dict(entry, path="Meshes/fake.fbx")]}, "v002"),
            [("Meshes/fake.fbx", "a" * 64, 123)])
        legacy = {"files": [dict(entry, source="E:\\Games\\Art\\Releases\\v002\\Meshes\\fake.fbx")]}
        self.assertEqual(
            portable.release_entries(legacy, "v002")[0][0], "Meshes/fake.fbx")

    def test_escape_and_duplicate_paths_are_rejected(self):
        for path in ("../private.bin", "/tmp/evil", "C:/Users/name/file", "../\\Windows"):
            with self.assertRaises(portable.AuditError):
                portable.safe_path(self.repo, path)
        with self.assertRaisesRegex(portable.AuditError, "Duplicate path"):
            portable.release_entries({"files": [
                {"path": "a.fbx", "sha256": "a" * 64},
                {"path": "a.fbx", "sha256": "b" * 64},
            ]}, "v002")

    def test_invalid_png_dimensions_rejected(self):
        with self.assertRaisesRegex(portable.AuditError, "Invalid PNG dimensions"):
            portable.check_signature("x.png", png(0, 4))

    def test_binding_and_roundtrip_texture_references(self):
        save_json(self.release / "Textures/material-bindings.json",
                  {"materials": {"M_Test": {"_MainTex": "demo.png"}}})
        save_json(self.release / "QA/roundtrip_report.json",
                  {"passed": True, "files": {"mesh.fbx": [{"textures": ["demo.png"]}]}})
        result = portable.validate_texture_dependencies(self.release, {
            "Textures/material-bindings.json", "Textures/demo.png", "QA/roundtrip_report.json",
        })
        self.assertEqual(result, {"material_bindings": 1, "qa_texture_references": 1})
        with self.assertRaisesRegex(portable.AuditError, "missing texture"):
            portable.validate_texture_dependencies(self.release, {
                "Textures/material-bindings.json", "QA/roundtrip_report.json",
            })

    def test_recipe_rejects_user_machine_drive_path(self):
        recipe = self.repo / "Source/Architecture/Bridge_Stone_A/v002"
        prior = recipe.parent / "v001"
        wall = self.repo / "Source/Architecture/Wall_Stone_Modular/v005"
        for path in (recipe / "build_bridge.py", recipe / "validate_bridge.py",
                     recipe / "bridge_contract.py", recipe / "bridge-site.json",
                     prior / "build_bridge.py", wall / "wall_geometry.py"):
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".json":
                save_json(path, {"asset_id": "ENV_Bridge_Stone_A",
                                 "version": "v002", "bridge_length": 10.8,
                                 "clear_walk_width": 2.86})
            else:
                path.write_text("# portable\n", encoding="utf-8")
        self.assertEqual(portable.audit_bridge_recipe(self.repo)["bridge_recipe_dependencies"], 6)
        (recipe / "build_bridge.py").write_text("bpy.load(r'C:\\Downloads\\asset.png')")
        with self.assertRaisesRegex(portable.AuditError, "Absolute Windows drive"):
            portable.audit_bridge_recipe(self.repo)

    def test_git_pointer_vs_hydrated_payload_and_missing_file(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"], check=True)
        path = self.repo / "Source/Architecture/model.blend"
        path.parent.mkdir(parents=True)
        payload = b"BLENDER-v440" + b"0123456789"
        oid = portable.sha256(payload)
        pointer = (b"version https://git-lfs.github.com/spec/v1\noid sha256:" +
                   oid.encode() + b"\nsize " + str(len(payload)).encode() + b"\n")
        path.write_bytes(pointer)
        subprocess.run(["git", "-C", str(self.repo), "add", "Source/Architecture/model.blend"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "fixture"], check=True)
        tracked = portable.tracked_files(self.repo)
        with self.assertRaisesRegex(portable.AuditError, "pointer not hydrated"):
            portable.audit_lfs(self.repo, tracked)
        path.write_bytes(payload)
        report = portable.audit_lfs(self.repo, tracked)
        self.assertEqual(report["unique_lfs_objects"], 1)
        self.assertEqual(report["tracked_lfs_paths"], 1)
        path.unlink()
        with self.assertRaisesRegex(portable.AuditError, "absent"):
            portable.audit_lfs(self.repo, tracked)
        self.assertEqual(portable.audit_lfs(self.repo, tracked, metadata_only=True)["unique_lfs_objects"], 1)

    def test_preserve_committed_text_bytes(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "config", "user.email", "test@example.invalid"], check=True)
        (self.repo / ".gitattributes").write_text("Releases/** -text\n")
        subprocess.run(["git", "-C", str(self.repo), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repo), "commit", "-qm", "fixture"], check=True)
        self.assertEqual(portable.audit_release(self.repo, self.manifest)["status"], "PASS")
        target = self.release / "README.md"
        target.write_bytes(target.read_bytes().replace(b"\r\n", b"\n"))
        doc = json.loads(self.manifest.read_text())
        doc["files_sha256"]["README.md"] = portable.sha256(target.read_bytes())
        save_json(self.manifest, doc)
        with self.assertRaisesRegex(portable.AuditError, "committed bytes"):
            portable.audit_release(self.repo, self.manifest)


if __name__ == "__main__":
    unittest.main()
