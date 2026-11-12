"""Download Pyodide's core for lesson 7 into apps/web/static/vendor/pyodide/.

Pinned and checksummed (ADR 0019): the release tarball's SHA-256 is a
constant here, each extracted file is checked against the committed
SHA256SUMS. Only the five named files are read from the archive (never
extractall), nothing from it is executed. Idempotent: if all five files are
present with the right hashes it says so and exits 0.

Run once per checkout: `make pyodide` (or `python3 -I scripts/fetch-pyodide.py`).
Standard library only.
"""

from __future__ import annotations

import hashlib
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

VERSION = "314.0.7"
URL = (
    f"https://github.com/pyodide/pyodide/releases/download/{VERSION}/pyodide-core-{VERSION}.tar.bz2"
)
TARBALL_SHA256 = "2abdcc2e35208af406e07724cffa85bc582ced97e9028383ecf5462541393f95"
DEST = Path(__file__).resolve().parents[1] / "apps/web/static/vendor/pyodide"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_sums() -> dict[str, str]:
    sums = {}
    for line in (DEST / "SHA256SUMS").read_text().splitlines():
        if line.strip():
            digest, name = line.split(None, 1)
            sums[name.strip()] = digest
    return sums


def installed(sums: dict[str, str]) -> bool:
    return all(
        (DEST / name).is_file() and sha256((DEST / name).read_bytes()) == digest
        for name, digest in sums.items()
    )


def main() -> int:
    sums = read_sums()
    if installed(sums):
        print(f"Pyodide {VERSION}: already installed in {DEST}")
        return 0
    work = Path(tempfile.mkdtemp(prefix="pyodide-"))
    try:
        archive = work / "core.tar.bz2"
        print(f"Downloading {URL}")
        with urllib.request.urlopen(URL, timeout=120) as response:  # noqa: S310
            archive.write_bytes(response.read())
        if sha256(archive.read_bytes()) != TARBALL_SHA256:
            print("The downloaded archive does not match the pinned SHA-256. Nothing installed.")
            return 1
        found: dict[str, bytes] = {}
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                name = Path(member.name).name
                if member.isfile() and name in sums and name not in found:
                    handle = tar.extractfile(member)
                    if handle is not None:
                        found[name] = handle.read()
        for name, digest in sums.items():
            if name not in found:
                print(f"{name} is missing from the archive. Nothing installed.")
                return 1
            if sha256(found[name]) != digest:
                print(f"{name} does not match SHA256SUMS. Nothing installed.")
                return 1
        DEST.mkdir(parents=True, exist_ok=True)
        for name, data in found.items():
            (DEST / name).write_bytes(data)
        print(f"Pyodide {VERSION}: installed {len(found)} files in {DEST}")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
