#!/usr/bin/env python3
"""Download a checksum-pinned official PocketBase binary for the local experiment."""

import argparse
import hashlib
import io
from pathlib import Path
import platform
import urllib.request
import zipfile

VERSION = "0.40.6"
ASSETS = {
    ("Darwin", "arm64"): ("darwin_arm64", "7f2f7544e9ee5994ab69f84b22a4ab9a3bcfed58c1dad7206d05ebeb753f968b"),
    ("Linux", "x86_64"): ("linux_amd64", "0e1f609158ed945f809f8a02ae012aa0427129c66ebb63c1aee76f2c0309373f"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    target = ASSETS.get((platform.system(), platform.machine()))
    if not target:
        raise SystemExit("Pinned binaries available for macOS arm64 and Linux amd64 only")
    suffix, digest = target
    url = f"https://github.com/pocketbase/pocketbase/releases/download/v{VERSION}/pocketbase_{VERSION}_{suffix}.zip"
    with urllib.request.urlopen(url, timeout=60) as response:
        archive = response.read()
    if hashlib.sha256(archive).hexdigest() != digest:
        raise SystemExit("PocketBase release archive checksum mismatch")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
        for name in ("pocketbase", "LICENSE.md"):
            if name in zipped.namelist():
                (args.output_dir / name).write_bytes(zipped.read(name))
    binary = args.output_dir / "pocketbase"
    binary.chmod(0o755)
    print(f"PocketBase {VERSION}: official archive SHA-256 verified; binary: {binary}")


if __name__ == "__main__":
    main()
