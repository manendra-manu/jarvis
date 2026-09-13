from __future__ import annotations

import datetime as dt
import json
import threading
import time
from pathlib import Path
from typing import Callable

from jarvis import config as _config

ON_REMINDER: Callable[[str], None] | None = None


def _load_reminders() -> list:
    f = _config.REMINDERS_FILE
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_reminders(items: list) -> None:
    _config.REMINDERS_FILE.write_text(
        json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> dt.datetime:
    return dt.datetime.now()


def _fmt_time(d: dt.datetime) -> str:
    h = d.strftime("%I").lstrip("0")
    m = d.strftime("%M")
    ap = "subah" if 5 <= d.hour < 12 else ("dopahar" if 12 <= d.hour < 17 else ("shaam" if 17 <= d.hour < 21 else "raat"))
    suffix = f" aur {m} minute" if m != "00" else ""
    return f"{ap} {h} baje{suffix}"


def _fire(reminder: dict) -> None:
    msg = reminder.get("message") or "aapka reminder"
    line = f"⏰ Reminder: {msg}  ({_fmt_time(_now())})"
    if "unittest" not in " ".join(__import__("sys").argv):
        print("\n" + "=" * 50 + f"\n{line}\n" + "=" * 50)
    if ON_REMINDER:
        try:
            ON_REMINDER(f"Sir, reminder ka time ho gaya hai. {msg}")
        except Exception:
            pass


class ReminderScheduler:
    """Daemon-thread reminder scheduler with file persistence."""

    INTERVAL = 2.0

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, name="jarvis-reminders", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        t = self._thread
        if t and t.is_alive():
            t.join(timeout=3)
        self._thread = None

    def _loop(self) -> None:
        while not self._stop.wait(self.INTERVAL):
            try:
                self.tick()
            except Exception as e:
                print(f"[reminder] tick error: {e}")

    def tick(self, now: dt.datetime | None = None) -> list:
        now = now or _now()
        items = _load_reminders()
        due = [r for r in items if dt.datetime.fromisoformat(r["at"]) <= now]
        if not due:
            return []
        keep = [r for r in items if r not in due]
        _save_reminders(keep)
        for r in due:
            _fire(r)
        return due


scheduler = ReminderScheduler()


def _parse_time_hint(text: str, base: dt.datetime) -> dt.datetime | None:
    """Parse Hinglish time expressions into datetime."""
    import re as _re
    t = (text or "").lower()
    t = t.translate(str.maketrans("०१२३४५६७८९", "0123456789"))
    t = (t.replace("शाम", "shaam").replace("सुबह", "subah").replace("रात", "raat")
           .replace("दोपहर", "dopahar").replace("मिनट", "minute").replace("घंटे", "hour")
           .replace("घंटा", "hour").replace("दिन", "day").replace("बाद", "baad")
           .replace("सेकंड", "second").replace("बजे", "baje"))
    m = (_re.search(r"(\d+)\s*(seconds?|secs?|minutes?|mins?|mints?|hours?|hrs?|ghantas?|ghantes?|days?|dins?)\s*(baad|bad|me|mein|after)", t)
         or _re.search(r"(\d+)\s*(seconds?|secs?|minutes?|mins?|mints?|hours?|hrs?|ghantas?|ghantes?|days?|dins?)\b", t))
    if m:
        n, unit = int(m.group(1)), m.group(2).rstrip("s")
        unit_map = {"sec": "second", "min": "minute", "mint": "minute", "hr": "hour",
                    "ghanta": "hour", "din": "day"}
        delta_map = {"second": dt.timedelta(seconds=n), "minute": dt.timedelta(minutes=n),
                     "hour": dt.timedelta(hours=n), "day": dt.timedelta(days=n)}
        unit = unit_map.get(unit, unit)
        delta = delta_map[unit]
        if delta.total_seconds() <= 0:
            return base
        return base + delta
    m = _re.search(r"(\d{1,2})\s*[:.]?\s*(\d{2})", t)
    if not m:
        m = _re.search(r"(\d{1,2})\s*(baje|am|pm|bajey)", t)
        if not m:
            m = _re.search(r"\b(\d{1,2})\b", t)
            if not m:
                return None
            h, mi = int(m.group(1)), 0
        else:
            h, mi = int(m.group(1)), 0
    else:
        h, mi = int(m.group(1)), int(m.group(2))
    if mi > 59 or h > 23:
        return None
    if "pm" in t or "shaam" in t or "evening" in t or "raat" in t or "night" in t or "dopahar" in t:
        if h < 12:
            h += 12
    elif "am" in t or "subah" in t or "morning" in t:
        if h == 12:
            h = 0
    target = base.replace(hour=h, minute=mi, second=0, microsecond=0)
    if target <= base:
        target += dt.timedelta(days=1)
    return target


def set_reminder(time_or_minutes: str, message: str = "") -> dict:
    """Set a reminder. Returns {ok, speech, text, tool}."""
    import re as _re
    s = str(time_or_minutes).strip()
    if _re.fullmatch(r"\d+(\.\d+)?", s):
        s = f"{s} minute baad"
    when = _parse_time_hint(s, _now())
    if not when:
        return {"ok": False, "speech": "Time samajh nahi aaya.", "text": s, "tool": "set_reminder"}
    message = (message or "reminder").strip()
    items = _load_reminders()
    rid = f"r{int(time.time() * 1000)}-{len(items)}"
    items.append({"id": rid, "at": when.isoformat(timespec="seconds"), "message": message})
    _save_reminders(items)
    scheduler.start()
    return {
        "ok": True,
        "speech": f"Theek hai, {_fmt_time(when)} '{message}' ka reminder laga diya.",
        "text": f"⏰ {when.strftime('%d %b %Y, %I:%M %p')} - {message}",
        "tool": "set_reminder",
    }


def list_reminders() -> dict:
    """List pending reminders."""
    items = sorted(_load_reminders(), key=lambda r: r["at"])
    future = [r for r in items if dt.datetime.fromisoformat(r["at"]) > _now()]
    if not future:
        return {"ok": True, "speech": "Abhi koi reminder set nahi hai.", "text": "", "tool": "list_reminders"}
    lines = [f"• {dt.datetime.fromisoformat(r['at']).strftime('%d %b, %I:%M %p')} - {r['message']}" for r in future]
    return {
        "ok": True,
        "speech": f"Aapke {len(future)} reminder hain: {future[0]['message']}, {_fmt_time(dt.datetime.fromisoformat(future[0]['at']))} ko.",
        "text": "\n".join(lines),
        "tool": "list_reminders",
    }


def delete_reminder(query: str = "") -> dict:
    """Delete reminders matching query."""
    items = _load_reminders()
    if not items:
        return {"ok": True, "speech": "Koi reminder hi nahi hai.", "text": "", "tool": "delete_reminder"}
    q = (query or "").lower().strip()
    if q in ("all", "sab", "sabhi", "saare"):
        _save_reminders([])
        return {"ok": True, "speech": "Saare reminder delete kar diye.", "text": "", "tool": "delete_reminder"}
    keep = [r for r in items if q not in r["message"].lower()]
    if len(keep) == len(items):
        return {"ok": False, "speech": "Wo reminder nahi mila.", "text": "\n".join(r["message"] for r in items), "tool": "delete_reminder"}
    _save_reminders(keep)
    return {"ok": True, "speech": "Reminder delete kar diya.", "text": "", "tool": "delete_reminder"}