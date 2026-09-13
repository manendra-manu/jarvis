"""
JARVIS ka Rules Engine (fast, pattern-based).
Zero API call - works offline.
"""
from __future__ import annotations

import re
from typing import Any

from jarvis import config as _config
from jarvis import tools as _tools

# Exact Greetings List - Substring Trap se bachne ke liye
EXACT_GREETINGS = {
    "hi", "hello", "hey", "namaste", "नमस्ते", "हेलो", "हाय",
    "jarvis", "जार्विस", "जरवेस", "hi jarvis", "hello jarvis",
    "hey jarvis", "ही जरवेस", "नमस्ते जार्विस"
}

# Priority List: Specific Rules ONLY
RULES: list[tuple[str, str, str]] = [
    # --- 1. Specific Actions ---
    (r"\b(reminder\s*list|mere\s*reminder|list\s*reminder|reminders\s*dikhao)\b", "list-reminders", "Reminders dikh rahi hoon..."),
    (r"\b(event\s*add|naya\s*event|calendar\s*mein\s*event|add\s*event)\b", "calendar-add", "Event add kar rahi hoon..."),
    (r"\b(file\s*dhoondho|file\s*search|file\s*dhundho|find\s*file)\b", "search-file", "File dhoondh rahi hoon..."),
    (r"\b(notes\s*dikhao|list\s*notes|mere\s*notes|all\s*notes)\b", "notes", "Notes dikh rahi hoon..."),

    # --- 2. System Check ---
    (r"\b(kya\s*haal|kaise\s*ho|haal\s*chaal|kaisa\s*hai)\b", "health", "Main theek hoon, shukriya! Aap batao, kya help chahiye?"),
    (r"\b(system\s*info|system\s*status|pc\s*info|computer\s*status)\b", "sysinfo", "System check kar rahi hoon..."),
    (r"\b(battery\s*status|battery\s*percentage|kitni\s*battery)\b", "battery", "Battery status check kar rahi hoon..."),

    # --- 3. Time & Date ---
    (r"\b(kitne\s*baje|samay\s*kya|time\s*kya\s*hai|time\s*batao)\b", "time", "Time check kar rahi hoon..."),
    (r"\b(aaj\s*kaun\s*sa\s*din|kya\s*tareekh|aaj\s*ki\s*date)\b", "date", "Date check kar rahi hoon..."),

    # --- 4. Utilities ---
    (r"\b(calculator|calc|hisaab|hisab|kitna\s*hota\s*hai|guna|bhag)\b", "math", "Hisab kar rahi hoon..."),
    (r"\b(reminder\s*laga|set\s*reminder|yaad\s*dilana|reminder\s*set)\b", "reminder", "Reminder set kar rahi hoon..."),
    (r"\b(note\s*karo|kuch\s*likho|note\s*banao)\b", "note", "Note bana rahi hoon..."),
    (r"\b(calendar|diary|agenda|schedule)\b", "calendar", "Calendar khol rahi hoon..."),

    # --- 5. Web & Apps ---
    (r"\b(google\s*karo|web\s*search|search\s*karo|internet\s*pe\s*dhoondho)\b", "search", "Search kar rahi hoon..."),
    (r"\b(website\s*kholo|open\s*site|web\s*kholo|browser\s*kholo)\b", "web", "Web khol rahi hoon..."),
    (r"\b(notepad\s*kholo|open\s*notepad)\b", "app", "Notepad khol rahi hoon..."),
    (r"\b(whatsapp\s*bhej|send\s*whatsapp)\b", "whatsapp", "WhatsApp message bhej rahi hoon..."),
    (r"\b(youtube\s*pe|play\s*on\s*youtube|youtube\s*chalao)\b", "youtube", "YouTube khol rahi hoon..."),

    # --- 6. Fun & Tools ---
    (r"\b(khabar|news|samachar)\b", "news", "News dikh rahi hoon..."),
    (r"\b(joke\s*sunao|chutkula|fun\s*joke)\b", "joke", "Ek joke suna rahi hoon..."),
    (r"\b(screenshot|screen\s*capture|ss\s*lo)\b", "screenshot", "Screenshot le rahi hoon..."),
    (r"\b(terminal\s*kholo|cmd\s*kholo)\b", "code", "Terminal khol rahi hoon..."),

    # --- 7. Exit ---
    (r"\b(stop|band\s*karo|quit|bye|exit)\b", "quit", "Theek hai, bye! 👋"),
]


def rule_engine(text: str) -> dict | None:
    """Agar koi rule match kare toh tool chala kar result return karo, warna AI ko do."""
    text_clean = text.lower().strip()
    if not text_clean:
        return None

    # 1. Exact Greeting Check (Sirf tabhi chalega jab sirf Hi/Hello bolenge)
    if text_clean in EXACT_GREETINGS:
        return {
            "speech": "Namaste! Main JARVIS hoon. Boliye main aapki kya madad karoon?",
            "text": "Namaste! Main JARVIS hoon. Boliye main aapki kya madad karoon?",
            "tool": "greeting",
            "ok": True,
            "stop": False,
        }

    # 2. Specific Rule Matching
    for pattern, tool, default_speech in RULES:
        if re.search(pattern, text_clean):
            try:
                res = _tools.run_tool(tool, {"query": text_clean})
                if res and isinstance(res, dict) and res.get("ok"):
                    return {
                        "speech": res.get("speech") or res.get("text") or default_speech,
                        "text": res.get("text") or res.get("speech") or default_speech,
                        "tool": tool,
                        "ok": True,
                        "stop": tool == "quit",
                    }
            except Exception:
                pass

            return {
                "speech": default_speech,
                "text": default_speech,
                "tool": tool,
                "ok": True,
                "stop": tool == "quit",
            }

    # Koi rule match nahi hua -> AI (Ollama / LLM) answer karega
    return None