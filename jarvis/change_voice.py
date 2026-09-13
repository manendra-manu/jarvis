#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
  JARVIS KI AWAAZ BADLO  (sirf FEMALE voices)
============================================================
Double-click: change-voice.bat
List dikhegi -> number type karo -> Enter -> awaaz save!
Phir run-jarvis.bat chalao, nayi awaaz mein bolegi.
============================================================
"""
import asyncio
import pathlib
import re
import sys

try:
    import edge_tts
except ImportError:
    sys.exit("edge-tts nahi mila. Pehle chalao:  pip install edge-tts")

import config  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent

# Tarjeeh ke locales pehle (Hindi -> Indian English -> baaki English)
LOCALE_ORDER = ["hi-IN", "en-IN", "en-US", "en-GB"]


def fetch_female() -> list:
    voices = asyncio.run(edge_tts.list_voices())
    # sirf kaam ki bhashayein: Hindi + English (100+ ki list se bachao)
    fem = [v for v in voices
           if v.get("Gender") == "Female" and v["Locale"] in LOCALE_ORDER]
    fem.sort(key=lambda v: (LOCALE_ORDER.index(v["Locale"]), v["ShortName"]))
    return fem


def save_voice(name: str) -> None:
    p = HERE / "config.py"
    s = p.read_text(encoding="utf-8")
    s = re.sub(r'EDGE_VOICE = "[^"]*"', f'EDGE_VOICE = "{name}"', s)
    p.write_text(s, encoding="utf-8")


def main():
    print()
    print("=" * 60)
    print("   JARVIS KI AWAAZ BADLO - female voices (free, Microsoft)")
    print("=" * 60)
    print()
    print("Awaaz ki list la rahi hoon... (2-3 sec)")
    voices = fetch_female()

    print()
    print("  No.  Awaaz                    Bhasha")
    print("  " + "-" * 52)
    for i, v in enumerate(voices, 1):
        tag = "  <-- abhi yahi chal rahi hai" if v["ShortName"] == config.EDGE_VOICE else ""
        lang = {"hi-IN": "Hindi", "en-IN": "English (India)",
                "en-US": "English (US)", "en-GB": "English (UK)"}.get(v["Locale"], v["Locale"])
        print(f"  {i:>2}.  {v['ShortName']:<24} {lang}{tag}")
    print()

    while True:
        try:
            ans = input(">>> Kis number ki awaaz chahiye? (Enter = cancel): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCancel.")
            return
        if not ans:
            print("Kuch nahi badla. Purani awaaz hi chalegi.")
            return
        if not ans.isdigit() or not (1 <= int(ans) <= len(voices)):
            print(f"1 se {len(voices)} ke beech number likho.")
            continue
        pick = voices[int(ans) - 1]["ShortName"]
        save_voice(pick)
        print()
        print("=" * 60)
        print(f"  🎀 AWAAZ BADAL GAYI: {pick}")
        print("=" * 60)
        print()
        print("  Ab run-jarvis.bat (ya web app) chalao - nayi awaaz!")
        print("  Sun ke pasand na aaye to dobara change-voice.bat chalao.")
        return


if __name__ == "__main__":
    main()
