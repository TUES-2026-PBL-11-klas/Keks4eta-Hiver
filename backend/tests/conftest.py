# Phase 5 — test configuration.
# Domain/application code imports as `from domain...` (package root = backend/src),
# so put src on sys.path for the test process.
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
