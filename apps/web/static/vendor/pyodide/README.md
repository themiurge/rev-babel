# Pyodide (lesson 7)

Pyodide 314.0.7 (CPython 3.14 compiled to WebAssembly), core only, no
packages. Released 2026-09-14 by the Pyodide project,
<https://github.com/pyodide/pyodide>. Licence: MPL-2.0 (`LICENSE`, here).

The runtime files (`pyodide.js`, `pyodide.asm.mjs`, `pyodide.asm.wasm`,
`python_stdlib.zip`, `pyodide-lock.json`, about 13.5 MB) are **not committed**:
they are gitignored and fetched by `scripts/fetch-pyodide.py` (`make pyodide`)
from the pinned release tarball, whose SHA-256 is checked, and then each file
against `SHA256SUMS` (committed, here). The script is idempotent.

Why: see [ADR 0019](../../../../../docs/decisions/0019-lesson-7-python-in-the-browser.md).

To refresh: change the version, tarball URL and tarball hash in
`scripts/fetch-pyodide.py`, update `SHA256SUMS` and `LICENSE`, and run the script.
