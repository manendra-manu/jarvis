#!/usr/bin/env python3
"""JARVIS Web Entry Point."""
from __future__ import annotations

import sys
from pathlib import Path

# Safe Parent Path Resolution
ROOT_DIR = Path(__file__).resolve().parent
if ROOT_DIR.name == "jarvis":
    sys.path.insert(0, str(ROOT_DIR.parent))
else:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from jarvis import webapp as _webapp
except ImportError:
    import webapp as _webapp  # Fallback import


def run_web(port: int | None = None) -> None:
    """Launch the Web Application."""
    _webapp.run(port)


def main() -> int:
    port = None
    # Agar user CLI se port pass kare: python web_cli.py 8080
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    run_web(port)
    return 0


if __name__ == "__main__":
    sys.exit(main())