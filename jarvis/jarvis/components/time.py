"""Time and date utilities for JARVIS."""
from __future__ import annotations

import datetime as dt

from jarvis import config as _config


def _now() -> dt.datetime:
    return dt.datetime.now()


def _fmt_time(d: dt.datetime) -> str:
    h = d.strftime("%I").lstrip("0")
    m = d.strftime("%M")
    ap = "subah" if 5 <= d.hour < 12 else ("dopahar" if 12 <= d.hour < 17 else ("shaam" if 17 <= d.hour < 21 else "raat"))
    suffix = f" aur {m} minute" if m != "00" else ""
    return f"{ap} {h} baje{suffix}"


def get_time() -> dict:
    now = _now()
    days = ["Somvaar", "Mangalvaar", "Budhvaar", "Guruvaar", "Shukravaar", "Shanivaar", "Ravivaar"]
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    speech = (f"Abhi {_fmt_time(now)} hain, aur {days[now.weekday()]} "
              f"{now.day} {months[now.month - 1]} {now.year} hai.")
    return {
        "ok": True,
        "speech": speech,
        "text": now.strftime("%A, %d %B %Y  %I:%M %p"),
        "tool": "get_time",
    }


def get_date() -> dict:
    return get_time()