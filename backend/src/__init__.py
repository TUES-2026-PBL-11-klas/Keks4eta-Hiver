"""Backend package root.

The codebase mixes two import styles: the app/infra layers use `src.<layer>`
(works when `backend/` is on sys.path, e.g. `uvicorn src.main:app`), while the
domain layer and tests use bare `<layer>` imports (work when `backend/src` is on
sys.path, e.g. pytest via conftest). To make `uvicorn src.main:app` boot without
forcing one convention, ensure this package's own directory is importable so the
bare `from domain...` / `from shared...` imports resolve too.
"""
import os
import sys

_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)
