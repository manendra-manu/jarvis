"""
JARVIS - Web server (FastAPI) with Dynamic Voice & Speed Control Settings.
"""
from __future__ import annotations

import json
import os
import queue
import threading
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from jarvis import config as _config
from jarvis import tools as _tools
from jarvis.brain import Brain, groq_key
from jarvis.speak import Speaker, say

WEB_DIR = Path(__file__).resolve().parent / "web"
WEB_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="JARVIS", version="2.0.0")

_brain_lock = threading.Lock()
_brain = Brain()
_thoughts: queue.Queue[str] = queue.Queue(maxsize=50)

def _put_thought(s: str) -> None:
    try:
        _thoughts.put_nowait(s)
    except Exception:
        pass

_brain.on_thought = _put_thought

# Runtime Dynamic Settings (Controlled directly from Web UI)
RUNTIME_SETTINGS = {
    "voice": "hi-IN-SwaraNeural",  # Default Hindi Female Voice
    "speed": "+35%",               # Default Speed (+35% Fast)
    "city": _config.DEFAULT_CITY
}


class ChatIn(BaseModel):
    text: str


class SpeakIn(BaseModel):
    text: str
    voice: str | None = None
    speed: str | None = None


class SettingsIn(BaseModel):
    voice: str | None = None
    speed: str | None = None
    city: str | None = None


@app.get("/")
def index():
    f = WEB_DIR / "index.html"
    if f.exists():
        return FileResponse(str(f))
    return JSONResponse({"error": "web/index.html nahi mila."})


@app.get("/api/status")
def status() -> dict:
    has_groq = bool(groq_key())
    return {
        "name": _config.ASSISTANT_NAME,
        "groq_online": has_groq,
        "current_voice": RUNTIME_SETTINGS["voice"],
        "current_speed": RUNTIME_SETTINGS["speed"],
        "current_city": RUNTIME_SETTINGS["city"],
        "language": "Hinglish",
        "tools": sorted(_tools.TOOLS.keys()),
    }


@app.get("/api/voices")
async def get_voices():
    """Return list of Female Voices for Web UI dropdown."""
    try:
        import edge_tts
        all_voices = await edge_tts.list_voices()
        locales = ["hi-IN", "en-IN", "en-US", "en-GB"]
        females = [
            {"name": v["ShortName"], "lang": v["Locale"], "friendly_name": f"{v['ShortName']} ({v['Locale']})"}
            for v in all_voices
            if v.get("Gender") == "Female" and v.get("Locale") in locales
        ]
        return {"ok": True, "voices": females}
    except Exception as e:
        return {"ok": False, "voices": [
            {"name": "hi-IN-SwaraNeural", "friendly_name": "Hindi - Swara"},
            {"name": "en-IN-NeerjaNeural", "friendly_name": "English India - Neerja"},
            {"name": "en-US-AvaNeural", "friendly_name": "English US - Ava"}
        ]}


@app.get("/api/settings")
def get_settings():
    return RUNTIME_SETTINGS


@app.post("/api/settings")
def update_settings(body: SettingsIn):
    """Update Voice, Speed, and City from Web UI directly."""
    if body.voice:
        RUNTIME_SETTINGS["voice"] = body.voice
    if body.speed:
        RUNTIME_SETTINGS["speed"] = body.speed
    if body.city:
        RUNTIME_SETTINGS["city"] = body.city
    return {"ok": True, "settings": RUNTIME_SETTINGS}


@app.post("/api/chat")
def chat(body: ChatIn) -> dict:
    with _brain_lock:
        res = _brain.think(body.text)
    res.setdefault("tools", [])
    return res


@app.post("/api/speak")
def speak(body: SpeakIn):
    """Generate audio with dynamic speed and voice from UI settings."""
    try:
        import asyncio
        import uuid
        import edge_tts

        out = _config.AUDIO_DIR / f"web_{uuid.uuid4().hex[:8]}.mp3"
        voice_to_use = body.voice or RUNTIME_SETTINGS["voice"]
        speed_to_use = body.speed or RUNTIME_SETTINGS["speed"]

        async def generate_audio() -> None:
            c = edge_tts.Communicate(body.text, voice=voice_to_use, rate=speed_to_use)
            await c.save(str(out))

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                def runner():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        new_loop.run_until_complete(generate_audio())
                    finally:
                        new_loop.close()
                pool.submit(runner).result()
        else:
            asyncio.run(generate_audio())

        data = b""
        if out.exists():
            data = out.read_bytes()
            try:
                out.unlink()
            except OSError:
                pass

        return Response(content=data, media_type="audio/mpeg")
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"{type(e).__name__}: {e}"}, status_code=500)


@app.post("/api/reset")
def reset() -> dict:
    with _brain_lock:
        _brain.reset()
    return {"ok": True}


app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


def run(port: int | None = None) -> None:
    """Start the web server."""
    import uvicorn
    port = port or _config.WEB_PORT
    uvicorn.run(app, host=_config.WEB_HOST, port=port, log_level="warning")


if __name__ == "__main__":
    run()