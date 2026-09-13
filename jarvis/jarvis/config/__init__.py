from __future__ import annotations

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIO_DIR = DATA_DIR / "audio"
LOG_DIR = DATA_DIR / "logs"
REMINDERS_FILE = DATA_DIR / "reminders.json"
NOTES_FILE = DATA_DIR / "notes.txt"
HISTORY_FILE = DATA_DIR / "history.jsonl"
SETTINGS_FILE = DATA_DIR / "settings.json"

for _d in (DATA_DIR, AUDIO_DIR, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

ASSISTANT_NAME = "JARVIS"

SYSTEM_PROMPT = f"""Tum {ASSISTANT_NAME} ho - ek bahut smart, friendly aur helpful personal AI assistant.
Tumhare user ka naam USER hai aur wo India mein rehta hai.

NIYAM (RULES):
1. Hamesha HINGLISH mein baat karo - matlab Hindi bhasha English letters (roman script) mein.
   Example: "Ho gaya! Maine 6 baje ka reminder laga diya hai."
2. Jawab CHHOTA rakho (1-3 line) kyunki tumhara jawab bola jayega (voice). Lambi list mat banao.
3. Agar koi kaam karna hai (reminder, file kholna, hisaab, weather, search) to tool use karo.
   Guess mat karo - tool se asli jankari lo.
4. Agar koi tool fail ho jaye to user ko saaf-saaf batao aur koi dusra rasta suggest karo.
5. Time aur date ke sawaal ke liye hamesha get_time tool use karo.
6. Kabhi bhi jhooth mat bolo. Nahi pata ho to "mujhe nahi pata" bolo.
7. Pyaar se baat karo, thoda filmy JARVIS style chalega, par faltu lambi baatein mat karo.
"""

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_TIMEOUT = 120
OLLAMA_TEMPERATURE = 0.4
OLLAMA_NUM_PREDICT = 300
OLLAMA_NUM_CTX = 2048
WARMUP_ON_START = True

GROQ_API_KEY = ""
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

USE_RULE_FALLBACK = True

STT_ENGINE = "google"
STT_LANGUAGE = "hi-IN"
LISTEN_TIMEOUT = 6
PHRASE_LIMIT = 15
WAKE_WORDS = ["jarvis", "hey jarvis", "hi jarvis", "ओके जार्विस"]
USE_WAKE_WORD = True

TTS_ENGINES = ["edge", "gTTS", "piper", "say"]
EDGE_VOICE = "hi-IN-SwaraNeural"
GTTS_LANG = "hi"
PIPER_VOICE_PATH = ""
SPEECH_RATE_WPM = 175
MAX_SPEAK_CHARS = 600

APP_COMMANDS = {
    "notepad": "notepad", "calculator": "calc", "calc": "calc",
    "paint": "mspaint", "explorer": "explorer", "file manager": "explorer",
    "task manager": "taskmgr", "cmd": "cmd", "command prompt": "cmd",
    "powershell": "powershell", "settings": "start ms-settings:",
    "word": "start winword", "excel": "start excel", "vscode": "code",
    "vs code": "code", "chrome": "start chrome", "browser": "start chrome",
    "spotify": "start spotify:", "whatsapp": "start https://web.whatsapp.com",
    "camera": "start microsoft.windows.camera:",
}

SEARCH_FOLDERS = [
    str(Path.home() / "Documents"),
    str(Path.home() / "Downloads"),
    str(Path.home() / "Desktop"),
]

DEFAULT_CITY = "Jabalpur"
WEB_HOST = "0.0.0.0"
WEB_PORT = 8000


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_settings(data: dict) -> None:
    SETTINGS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get(name: str, default=None):
    return load_settings().get(name, globals().get(name, default))
