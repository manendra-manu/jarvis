"""Notes management for JARVIS."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from jarvis import config as _config


def add_note(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"ok": False, "speech": "Kya note karna hai?", "text": "", "tool": "add_note"}
    stamp = dt.datetime.now().strftime("%d-%m-%Y %H:%M")
    content = _config.NOTES_FILE.read_text(encoding="utf-8") if _config.NOTES_FILE.exists() else ""
    _config.NOTES_FILE.write_text(content + f"[{stamp}] {text}\n", encoding="utf-8")
    return {"ok": True, "speech": "Note kar liya.", "text": f"\U0001f4dd [{stamp}] {text}", "tool": "add_note"}


def read_notes() -> dict:
    f = _config.NOTES_FILE
    if not f.exists() or not f.read_text(encoding="utf-8").strip():
        return {"ok": True, "speech": "Abhi koi note nahi hai.", "text": "", "tool": "read_notes"}
    lines = f.read_text(encoding="utf-8").strip().splitlines()
    last = lines[-5:]
    return {
        "ok": True,
        "speech": f"Aapke {len(lines)} note hain. Sabse naya: {last[-1].split('] ', 1)[-1]}",
        "text": "\n".join(last),
        "tool": "read_notes",
    }
