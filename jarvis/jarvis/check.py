#!/usr/bin/env python3
"""JARVIS Health Check - kya ready hai, kya missing hai ek nazar mein."""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

# Fix sys.path to allow `import jarvis` properly
ROOT_DIR = Path(__file__).resolve().parent
if ROOT_DIR.name == "jarvis":
    sys.path.insert(0, str(ROOT_DIR.parent))
else:
    sys.path.insert(0, str(ROOT_DIR))

OK, WARN, BAD = "[OK]", "[!!]", "[XX]"


def line(flag: str, name: str, msg: str = "") -> None:
    print(f"  {flag} {name:<22}: {msg}")


def has(module: str) -> bool:
    try:
        importlib.import_module(module)
        return True
    except Exception:
        return False


def main() -> int:
    problems = 0
    print("\n" + "=" * 62)
    print("   J A R V I S   -   KYA READY HAI?   (Health Check)")
    print("=" * 62 + "\n")

    # 1. Python Version Check
    v = sys.version_info
    if v >= (3, 10):
        line(OK, "Python", sys.version.split()[0])
    else:
        line(BAD, "Python", f"{sys.version.split()[0]}  <-- 3.10 ya naya chahiye!")
        problems += 1

    # 2. Package Check
    pkgs = [
        ("requests", "requests", BAD, "pip install requests"),
        ("fastapi + uvicorn", "fastapi", BAD, "pip install fastapi uvicorn[standard]"),
        ("sun'na (STT)", "speech_recognition", BAD, "pip install SpeechRecognition"),
        ("mic driver (sounddevice)", "sounddevice", BAD, "pip install sounddevice numpy"),
        ("awaaz - edge (female)", "edge_tts", WARN, "pip install edge-tts"),
        ("awaaz - gTTS (backup)", "gTTS", WARN, "pip install gTTS"),
        ("audio player", "playsound", WARN, "pip install playsound==1.2.2"),
        ("WhatsApp bhejna", "pywhatkit", WARN, "pip install pywhatkit"),
        ("system info", "psutil", WARN, "pip install psutil"),
        ("screenshot", "pyautogui", WARN, "pip install pyautogui"),
        ("offline STT (vosk)", "vosk", WARN, "optional - pip install vosk"),
        ("mic driver (pyaudio alt)", "pyaudio", WARN, "optional - sounddevice kaafi hai"),
        ('"Hey JARVIS" wake word', "openwakeword", WARN, "optional - pip install openwakeword"),
    ]
    for label, mod, severity, fix in pkgs:
        if has(mod):
            line(OK, label, "installed")
        else:
            line(severity, label, fix)
            if severity == BAD:
                problems += 1

    # 3. Ollama Check
    try:
        from jarvis import brain as brainmod
        if brainmod.ollama_alive():
            models = brainmod.ollama_models()
            line(OK, "Ollama (AI dimaag)", "CHALU hai")
            if models:
                line(OK, "  models", ", ".join(models))
            else:
                line(WARN, "  models", "koi model nahi -> CMD mein: ollama pull llama3.1:8b")
        else:
            line(WARN, "Ollama (AI dimaag)",
                 "BAND - basic commands phir bhi chalenge. Smart jawab: ollama.com/download")
    except Exception as e:
        line(BAD, "Ollama check", f"error: {e}")
        problems += 1

    # 4. Reliable Internet Check
    try:
        import requests
        requests.get("https://1.1.1.1", timeout=3)
        line(OK, "Internet", "hai (mausam/search/awaaz chalega)")
    except Exception:
        line(WARN, "Internet", "nahi mil raha - mausam/search/edge-voice nahi chalega")

    # 5. JARVIS Tools Check
    try:
        from jarvis import tools as jtools
        line(OK, "Tools (pkg)", f"{len(jtools.TOOLS)} tools ready, {len(jtools.TOOL_SCHEMAS)} AI schemas")
    except Exception as e:
        line(BAD, "Tools (pkg)", f"{e}")
        problems += 1

    # 6. Data Directory Check
    data_dir = ROOT_DIR / "data"
    audio_dir = data_dir / "audio"
    data_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    line(OK, "data folder", str(data_dir))

    # 7. Unit Tests Check
    tests_dir = ROOT_DIR / "tests"
    if tests_dir.exists():
        print("\n  Test chal rahe hain...")
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir)],
                           capture_output=True, text=True)
        tail = (r.stderr or r.stdout).strip().splitlines()
        if r.returncode == 0:
            line(OK, "Tests", tail[-3] if len(tail) >= 3 else "sab pass")
        else:
            line(BAD, "Tests", "FAIL")
            print("\n".join("      " + x for x in tail[-15:]))
            problems += 1
    else:
        line(OK, "Tests", "skipped (tests folder nahi mila)")

    # Verdict Summary
    print("\n" + "=" * 62)
    if problems == 0:
        print("  SAB READY HAI! Ab chalao:")
        print("     python -m jarvis.main   -> mic se baat karo")
        print("     python -m jarvis.webapp -> browser wala JARVIS (http://localhost:8000)")
    else:
        print(f"  {problems} cheez theek karni hai (upar [XX] wali lines dekho).")
    print("=" * 62 + "\n")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())