from __future__ import annotations

import inspect
import webbrowser

from jarvis.components.math import do_math
from jarvis.components.notes import add_note, read_notes
from jarvis.components.reminders import (
    delete_reminder, list_reminders, scheduler, set_reminder,
)
from jarvis.components.search import (
    get_weather, web_search, wikipedia_summary,
)
from jarvis.components.system import (
    cancel_shutdown, compliment, IS_WINDOWS, joke, open_app, open_website,
    play_media, screenshot, search_file, send_email, send_whatsapp,
    system_info, system_control, volume,
    get_time, get_date,
)

TOOLS = {
    "get_time": get_time, "get_date": get_date, "do_math": do_math,
    "set_reminder": set_reminder, "list_reminders": list_reminders,
    "delete_reminder": delete_reminder,
    "add_note": add_note, "read_notes": read_notes,
    "web_search": web_search, "wikipedia_summary": wikipedia_summary,
    "get_weather": get_weather,
    "open_app": open_app, "open_website": open_website,
    "play_media": play_media, "volume": volume, "search_file": search_file,
    "system_info": system_info, "system_control": system_control,
    "cancel_shutdown": cancel_shutdown, "screenshot": screenshot,
    "send_whatsapp": send_whatsapp, "send_email": send_email,
    "joke": joke, "compliment": compliment,
}

# Alias Mapping: Rule Engine ke chote naamo ko sahi tool se jodne ke liye
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
    "whatsapp": "send_whatsapp",
    "media": "play_media",
    "youtube": "play_media",
    "search-file": "search_file",
}

TOOL_SCHEMAS = [
    {"type": "function", "function": {"name": "get_time", "description": "Abhi ka time aur date batao.",
      "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "get_date", "description": "Aaj ki date aur din batao.",
      "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "do_math", "description": "Maths ka hisaab lagao.",
      "parameters": {"type": "object", "properties": {"expression": {"type": "string", "description": "e.g. 250*4+15"}},
      "required": ["expression"]}}},
    {"type": "function", "function": {"name": "set_reminder", "description": "Reminder set karo.",
      "parameters": {"type": "object", "properties": {
        "time_or_minutes": {"type": "string", "description": "10 minute baad ya 6 baje ya shaam 7:30"},
        "message": {"type": "string", "description": "kis cheez ka reminder"}}, "required": ["time_or_minutes"]}}},
    {"type": "function", "function": {"name": "list_reminders", "description": "Saare pending reminder dikha.",
      "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "delete_reminder", "description": "Reminder delete karo.",
      "parameters": {"type": "object", "properties": {"query": {"type": "string", "description": "keyword ya all"}}, "required": []}}},
    {"type": "function", "function": {"name": "add_note", "description": "Ek note save karo.",
      "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}}},
    {"type": "function", "function": {"name": "read_notes", "description": "Saved notes padho.",
      "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "web_search", "description": "Internet pe search karo (DuckDuckGo).",
      "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "wikipedia_summary", "description": "Kisi topic ki detail jankari (Wikipedia).",
      "parameters": {"type": "object", "properties": {"topic": {"type": "string"}, "sentences": {"type": "integer"}}, "required": ["topic"]}}},
    {"type": "function", "function": {"name": "get_weather", "description": "Kisi sheher ka mausam.",
      "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "open_app", "description": "Computer ki app ya website kholo.",
      "parameters": {"type": "object", "properties": {"app": {"type": "string"}}, "required": ["app"]}}},
    {"type": "function", "function": {"name": "open_website", "description": "Website kholo.",
      "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "play_media", "description": "YouTube/Spotify pe song ya video chalao.",
      "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "kind": {"type": "string", "enum": ["youtube", "song", "spotify"]}}, "required": []}}},
    {"type": "function", "function": {"name": "volume", "description": "Volume up/down/mute.",
      "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["up", "down", "mute"]}}, "required": []}}},
    {"type": "function", "function": {"name": "search_file", "description": "Computer mein file dhoondho.",
      "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "folder": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "system_info", "description": "Battery, CPU, RAM ki jankari.",
      "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "system_control", "description": "PC shutdown/restart/lock/sleep.",
      "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["shutdown", "restart", "lock", "sleep"]}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "cancel_shutdown", "description": "Shutdown cancel karo.",
      "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "screenshot", "description": "Screen ka photo lo.",
      "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "send_whatsapp", "description": "WhatsApp message bhejo.",
      "parameters": {"type": "object", "properties": {"number": {"type": "string", "description": "+91... number"}, "message": {"type": "string"}}, "required": ["number", "message"]}}},
    {"type": "function", "function": {"name": "send_email", "description": "Email draft kholo.",
      "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to"]}}},
    {"type": "function", "function": {"name": "joke", "description": "Ek joke sunao.",
      "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "compliment", "description": "User ki tareef karo.",
      "parameters": {"type": "object", "properties": {}, "required": []}}},
]


def run_tool(name: str, args: dict | None = None) -> dict:
    args = args or {}
    
    # 1. Resolve Alias Name
    actual_name = ALIASES.get(name, name)
    fn = TOOLS.get(actual_name)
    
    if not fn:
        return {"ok": False, "speech": f"{name} naam ka tool nahi hai.", "text": name, "tool": name}

    try:
        # 2. Smart Inspection: Pass only parameters accepted by the target function
        sig = inspect.signature(fn)
        has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
        
        if not has_kwargs:
            filtered_args = {k: v for k, v in args.items() if k in sig.parameters}
        else:
            filtered_args = args

        res = fn(**filtered_args)

        if not isinstance(res, dict):
            res = {"ok": True, "speech": str(res), "text": str(res)}

        res.setdefault("tool", actual_name)
        res.setdefault("ok", True)
        return res

    except TypeError:
        # Fallback if argument filtering fails, try running with no arguments
        try:
            res = fn()
            if not isinstance(res, dict):
                res = {"ok": True, "speech": str(res), "text": str(res)}
            res.setdefault("tool", actual_name)
            res.setdefault("ok", True)
            return res
        except Exception as e:
            return {"ok": False, "speech": "Tool galat tarike se call hua.", "text": f"{name}: {e}", "tool": name}

    except Exception as e:
        return {"ok": False, "speech": "Tool chalne mein dikkat aayi.", "text": f"{name}: {type(e).__name__}: {e}", "tool": name}