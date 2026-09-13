#!/usr/bin/env python3
"""JARVIS - setup_logging helper."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

def setup_logging() -> None:
    log_dir = Path(__file__).resolve().parent.parent.parent / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "jarvis.log", encoding="utf-8"),
        ],
    )
    logging.getLogger("jarvis").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)