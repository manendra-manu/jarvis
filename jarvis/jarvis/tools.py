"""
JARVIS - Cloud-Safe Tools Executor & Aliases.
"""
from __future__ import annotations

import inspect
import sys

from jarvis.components.math import do_math
from jarvis.components.notes import add_note, read_notes
from jarvis.components.reminders import (
    delete_reminder, list_reminders, scheduler, set_reminder,
)
from jarvis.components.search import (
    get_weather, web_search, wikipedia_summary,
)
from jarvis.components.system import (
    cancel_shutdown, compliment, joke,
    system_info, system_control, get_time, get_date,
)

# Cloud-Safe System / Media Handlers
def safe_play_media(query: str = "", kind: str = "youtube") -> dict:
    if query:
        search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        return {
            "ok": True,
            "speech": f"YouTube par {query} search kar diya hai. Aap yeh link khol sakte ho: {search_url}",
            "text": f"YouTube Search Link: {search_url}",
            "tool": "play_media"
        }
    return {"ok": True, "speech": "YouTube khol diya hai.", "text": "https://youtube.com", "tool": "play_media"}


def safe_open_app(app: str = "") -> dict:
    return {
        "ok": True,
        "speech": f"Main cloud server par hoon, isliye aapke PC par {app or 'app'} nahi khol sakti.",
        "text": f"Cloud Server: Cannot launch local app '{app}'",
        "tool": "open_app"
    }


def safe_screenshot(path: str = "") -> dict:
    return {
        "ok": False,
        "speech": "Cloud server par screen nahi hoti, isliye screenshot nahi le sakti.",
        "text": "Cloud Server: Screenshot unavailable",
        "tool": "screenshot"
    }


TOOLS = {
    "get_time": get_time, "get_date": get_date, "do_math": do_math,
    "set_reminder": set_reminder, "list_reminders": list_reminders,
    "delete_reminder": delete_reminder,
    "add_note": add_note, "read_notes": read_notes,
    "web_search": web_search, "wikipedia_summary": wikipedia_summary,
    "get_weather": get_weather,
    "open_app": safe_open_app, "open_website": safe_play_media,
    "play_media": safe_play_media, "search_file": safe_open_app,
    "system_info": system_info, "system_control": system_control,
    "cancel_shutdown": cancel_shutdown, "screenshot": safe_screenshot,
    "joke": joke, "compliment": compliment,
}

ALIASES = {
    "time": "get_time",
    "date": "get_date",
    "sysinfo": "system_info",
    "health": "system_info",
    "battery": "system_info",
    "math": "do_math",
    "reminder": "set_reminder",
    "list-reminders": "list_reminders",
    "note": "add_note",
    "notes": "read_notes",
    "search": "web_search",
    "weather": "get_weather",
    "app": "open_app",
    "web": "open_website",
    "whatsapp": "open_app",
    "media": "play_media",
    "youtube": "play_media",
    "search-file": "search_file",
}

TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "get_time", "description": "Abhi ka time aur date batao.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_date", "description": "Aaj ki date aur din batao.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "do_math", "description": "Maths ka hisaab lagao.", "parameters": {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}}},
    {"type": "function", "function": {"name": "get_weather", "description": "Kisi sheher ka mausam.", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "web_search", "description": "Internet pe search karo.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "play_media", "description": "YouTube song/video search.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "joke", "description": "Joke sunao.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]


def run_tool(name: str, args: dict | None = None) -> dict:
    args = args or {}
    actual_name = ALIASES.get(name, name)
    fn = TOOLS.get(actual_name)

    if not fn:
        return {"ok": True, "speech": f"{name} ke baare mein jankari nahi hai.", "text": name, "tool": name}

    try:
        sig = inspect.signature(fn)
        has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        filtered_args = args if has_kwargs else {k: v for k, v in args.items() if k in sig.parameters}

        res = fn(**filtered_args)
        if not isinstance(res, dict):
            res = {"ok": True, "speech": str(res), "text": str(res)}

        res.setdefault("tool", actual_name)
        res.setdefault("ok", True)
        return res
    except Exception as e:
        return {
            "ok": True,
            "speech": f"{actual_name} process karne mein dikkat aayi.",
            "text": str(e),
            "tool": actual_name
        }