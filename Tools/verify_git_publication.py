"""Read-only audit: committed LFS pointers, local payloads, and Bridge v002 hashes."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BINARY_SUFFIXES = {".blend", ".fbx", ".png", ".jpg", ".jpeg", ".exr", ".tga", ".psd"}


def git(*args, stdin=None):
    return subprocess.run(
        ["git", *args], cwd=ROOT, input=stdin, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=True).stdout


def committed_blobs(paths):
    requests = "".join("HEAD:" + path + "\n" for path in paths).encode("utf-8")
    output = git("cat-file", "--batch", stdin=requests)
    offset = 0
    result = {}
    for path in paths:
        end = output.index(b"\n", offset)
        header = output[offset:end].split()
        assert len(header) == 3 and header[1] == b"blob", (path, header)
        count = int(header[2])
        start = end + 1
        result[path] = output[start:start + count]
        assert output[start + count:start + count + 1] == b"\n"
        offset = start + count + 1
    assert offset == len(output)
    return result


def main():
    tracked = git("ls-files", "-z").decode("utf-8").rstrip("\0").split("\0")
    binaries = [path for path in tracked if path.startswith(("Source/", "Releases/"))
                and Path(path).suffix.lower() in BINARY_SUFFIXES]
    blobs = committed_blobs(binaries)
    unique = {}
    for path, pointer in blobs.items():
        assert pointer.startswith(b"version https://git-lfs.github.com/spec/v1\n"), path
        oid = re.search(rb"oid sha256:([a-f0-9]{64})", pointer).group(1).decode("ascii")
        size = int(re.search(rb"size ([0-9]+)", pointer).group(1))
        payload = (ROOT / path).read_bytes()
        assert len(payload) == size and hashlib.sha256(payload).hexdigest() == oid, path
        unique[oid] = size

    release = ROOT / "Releases/Bridge_Stone_A/v002"
    manifest = json.loads((release / "release.json").read_text(encoding="utf-8"))
    release_paths = ["Releases/Bridge_Stone_A/v002/" + key for key in manifest["files_sha256"]]
    text_paths = [path for path in release_paths if Path(path).suffix.lower() not in BINARY_SUFFIXES]
    release_blobs = committed_blobs(text_paths)
    for relative, expected in manifest["files_sha256"].items():
        payload = (release / relative).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == expected, relative
        key = "Releases/Bridge_Stone_A/v002/" + relative
        if key in release_blobs:
            assert hashlib.sha256(release_blobs[key]).hexdigest() == expected, (relative, "Git changed raw bytes")
    print("ART_PUBLICATION_VERIFIED", len(binaries), "LFS paths,", len(unique),
          "unique objects,", sum(unique.values()), "unique bytes; Bridge v002 manifest PASS")


if __name__ == "__main__":
    main()
