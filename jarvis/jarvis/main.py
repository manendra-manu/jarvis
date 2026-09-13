"""
J A R V I S  -  Desktop Voice Assistant  (Hinglish)
Main entry point for the JARVIS desktop and CLI application.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import traceback
from pathlib import Path

# Fix sys.path to ensure 'from jarvis import ...' always works
ROOT_DIR = Path(__file__).resolve().parent
if ROOT_DIR.name == "jarvis":
    sys.path.insert(0, str(ROOT_DIR.parent))
else:
    sys.path.insert(0, str(ROOT_DIR))

from jarvis import config as _config
from jarvis import tools as _tools
from jarvis import brain as _brain_mod
from jarvis.brain import Brain, ollama_alive, ollama_models
from jarvis.speak import Speaker
from jarvis.listen import Listener, NoMicError

logger = logging.getLogger("jarvis")

_SPEAKER: Speaker | None = None


def _on_reminder(text: str) -> None:
    if _SPEAKER:
        _SPEAKER.say(text, block=True)
    else:
        print("\n🔔 Reminder: " + text)


_tools.ON_REMINDER = _on_reminder

BANNER = r"""
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ██║███████║██████╔╝██║   ██║██║███████╗
 ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
 ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
         Aapki personal voice assistant  |  Hinglish mode
"""

CMDS = """
 ─────────────────────────────────────────────────────────────
  Aap ye bol sakte ho:
    "kitne baje hain"                 "shaam 6 baje reminder laga"
    "250 guna 4 kitna hota hai"      "note karo doodh lana hai"
    "jabalpur ka mausam"              "notepad kholo"
    "youtube pe arijit singh chalao"  "resume file dhoondho"
    "virat kohli kaun hai"            "whatsapp bhej 9876543210 main aa raha hoon"
    "system info"                      "ek joke sunao"
 ─────────────────────────────────────────────────────────────
"""


def _print(text: str, color: str = "") -> None:
    codes = {
        "green": "\033[92m", "cyan": "\033[96m", "yellow": "\033[93m",
        "red": "\033[91m", "dim": "\033[90m", "bold": "\033[1m", "": ""
    }
    out = f"{codes.get(color, '')}{text}\033[0m" if color else text
    print(out, flush=True)


def banner() -> None:
    _print(BANNER, "cyan")
    
    if _brain_mod.groq_key():
        _print(f"  ☁️  Cloud brain: ON (Groq {_config.GROQ_MODEL}) - smart jawab 1-2 sec", "green")
    
    ok = ollama_alive()
    if ok:
        models = ollama_models()
        _print(f"  🧠 Ollama: ONLINE   models: {', '.join(models) or '(koi model nahi)'}", "green")
        if not models:
            _print("     Install karo:  ollama pull llama3.1:8b", "yellow")
        _print("     Smart jawab slow lage to halka model: python -m jarvis.main --model llama3.2:3b", "dim")
    else:
        _print("  🧠 Ollama: OFFLINE  -> basic commands bina AI ke bhi chalenge (rule engine)", "yellow")
        _print("     Full brain ke liye: https://ollama.com/download  phir  ollama pull llama3.1:8b", "dim")
    
    if _SPEAKER:
        eng = _SPEAKER.available()
        _print(f"  🔊 Awaaz: {', '.join(eng) or 'koi TTS engine nahi (pip install edge-tts gTTS playsound)'}",
               "green" if eng else "red")
    _print(CMDS)


def handle(text: str, brain: Brain) -> dict:
    """Process a single command: think -> speak -> display."""
    _print(f"\n🗣  Aap: {text}", "bold")
    t0 = time.time()
    try:
        res = brain.think(text)
    except Exception:
        traceback.print_exc()
        res = {"ok": False, "speech": "Kuch gadbad ho gayi, dobara boliye.", "text": ""}

    src = {"rule": "rule-engine", "llm": f"ollama:{brain.model}", "fallback": "fallback"}.get(
        res.get("source"), "?")
    
    tools_used = res.get("tools") or ([res.get("tool")] if res.get("tool") else [])
    tool_str = ",".join([t for t in tools_used if t]) or "-"

    _print(f"🤖 JARVIS: {res.get('speech', '')}", "green")
    if res.get("text") and res["text"] != res.get("speech"):
        _print("   " + str(res["text"]).replace("\n", "\n   "), "dim")
    _print(f"   [{src} | tool: {tool_str} | {time.time() - t0:.1f}s]", "dim")
    return res


def text_mode(brain: Brain) -> None:
    """Text-only mode - type commands instead of speaking."""
    _print("TYPE MODE - likh kar baat karo.  'exit' = band\n")
    while True:
        try:
            text = input("\nAap> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text.lower() in ("exit", "quit", "bye", "band karo"):
            _print("Bye! 👋", "cyan")
            break
        res = handle(text, brain)
        if res.get("stop"):
            break


def voice_mode(brain: Brain, use_wake: bool) -> None:
    """Voice mode - listen and respond via microphone."""
    global _SPEAKER
    _SPEAKER = _SPEAKER or Speaker()
    lis = Listener()

    backend = lis.backend_name()
    if backend == "none":
        _print("\n  [X] MIC ka koi driver installed nahi hai!", "red")
        _print("      Ek command chalao:")
        _print("          pip install sounddevice numpy", "bold")
        _print("\n      Tab tak ye use karo:")
        _print("          python -m jarvis.main --text     (type karke baat karo)")
        if _SPEAKER:
            _SPEAKER.say("Mic driver install nahi hai. pip install sounddevice numpy chalao.", block=True)
        return

    mics = lis.list_microphones()
    _print(f"🎤 Mic backend: {backend}  |  Microphones: {mics}", "dim")
    if _SPEAKER:
        _SPEAKER.say("Namaste! Main JARVIS hoon. Boliye main sun rahi hoon.", block=True)

    fails = 0

    def on_wake() -> None:
        nonlocal fails
        _print("\n✨ 'JARVIS' sun liya - boliye...", "yellow")
        if _SPEAKER:
            _SPEAKER.say("Ji boss?", block=True)  # Fixed: block=True to prevent self-listening
        
        heard = lis.listen_once(timeout=_config.LISTEN_TIMEOUT + 2)
        if heard:
            res = handle(heard, brain)
            if res.get("speech") and _SPEAKER:
                _SPEAKER.say(res["speech"], block=True)  # Fixed: block=True
        else:
            if _SPEAKER:
                _SPEAKER.say("Maine kuch suna nahi.", block=True)

    try:
        if use_wake:
            lis.listen_for_wake_word(on_wake=on_wake)
            return

        _print("Har baar sun rahi hoon. Band karne ke liye Ctrl+C\n", "dim")
        idle = 0
        while True:
            try:
                heard = lis.listen_once()
                fails = 0
            except NoMicError as e:
                _print(f"\n[X] Mic band ho gaya: {e}", "red")
                break
            except Exception as e:
                fails += 1
                if fails == 1:
                    _print(f"[STT] {type(e).__name__}: {e}", "red")
                if fails >= 3:
                    _print("\n[X] Mic baar-baar fail ho raha hai. 'pip install sounddevice numpy' karo.", "red")
                    break
                time.sleep(0.5)
                continue

            if not heard:
                idle += 1
                if idle % 12 == 0:
                    _print("   (sun rahi hoon...)", "dim")
                time.sleep(0.2)
                continue

            idle = 0
            res = handle(heard, brain)
            if res.get("speech") and _SPEAKER:
                _SPEAKER.say(res["speech"], block=True)
            if res.get("stop"):
                break
    except KeyboardInterrupt:
        pass
    _print("\nBye! 👋", "cyan")


def main() -> int:
    """Main entry point."""
    ap = argparse.ArgumentParser(description="JARVIS - Hinglish voice assistant")
    ap.add_argument("--text", action="store_true", help="type karke baat karo (mic nahi)")
    ap.add_argument("--nowake", action="store_true", help="wake word band, har baar suno")
    ap.add_argument("--web", action="store_true", help="browser wala JARVIS kholo")
    ap.add_argument("--model", default=None, help="Ollama model (e.g. llama3.2:3b)")
    ap.add_argument("--host", default=None, help="Ollama host (default http://127.0.0.1:11434)")
    ap.add_argument("--port", type=int, default=_config.WEB_PORT)
    ap.add_argument("--mute", action="store_true", help="awaaz band (sirf text)")
    ap.add_argument("--voice", default=None, help="edge-tts voice name")
    args = ap.parse_args()

    global _SPEAKER
    _SPEAKER = Speaker(muted=args.mute, voice=args.voice or _config.EDGE_VOICE)

    # Start Background Reminder Scheduler
    try:
        _tools.scheduler.start()
    except Exception:
        pass

    try:
        if args.web:
            os.environ["JARVIS_MODEL"] = args.model or ""
            os.environ["JARVIS_PORT"] = str(args.port)
            from jarvis import webapp
            webapp.run(port=args.port)
            return 0

        model = args.model
        if not model:
            avail = ollama_models(args.host)
            for pref in ("llama3.2:3b", "llama3.1:8b"):
                if any(m.startswith(pref) for m in avail):
                    model = pref
                    break

        brain = Brain(model=model, host=args.host)
        banner()

        if _config.WARMUP_ON_START and ollama_alive(args.host):
            import threading
            def _warm() -> None:
                try:
                    import requests as _rq
                    _rq.post(f"{_config.OLLAMA_HOST}/api/generate",
                             json={"model": brain.model, "prompt": "hi", "stream": False,
                                   "options": {"num_predict": 4, "num_ctx": _config.OLLAMA_NUM_CTX}},
                             timeout=180)
                except Exception:
                    pass
            threading.Thread(target=_warm, daemon=True).start()
            _print("  🔥 Model background mein load ho raha hai (~20-30s)", "dim")

        if args.text:
            text_mode(brain)
        else:
            voice_mode(brain, use_wake=_config.USE_WAKE_WORD and not args.nowake)

    finally:
        # Graceful Scheduler Shutdown
        try:
            if hasattr(_tools.scheduler, "shutdown"):
                _tools.scheduler.shutdown(wait=False)
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nBye!")