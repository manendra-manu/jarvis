"""JARVIS - Personal Voice Assistant CLI Entrypoint."""
from __future__ import annotations

import sys
from pathlib import Path

# Project root directory ko sys.path mein jodne ka safe tareeka
ROOT_DIR = Path(__file__).resolve().parent
if ROOT_DIR.name == "jarvis":
    sys.path.insert(0, str(ROOT_DIR.parent))
else:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from jarvis import main as _jarvis
except ImportError:
    import main as _jarvis


def main() -> int:
    return _jarvis.main()


if __name__ == "__main__":
    sys.exit(main())