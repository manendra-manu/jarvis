"""
JARVIS - Web server (FastAPI) for browser/phone access.
Thread-safe with singleton brain instance & Fast Speech Rate.
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
from jarvis.brain import Brain, ollama_alive, ollama_models
from jarvis.speak import Speaker, say

WEB_DIR = Path(__file__).resolve().parent / "web"
WEB_DIR.mkdir(parents=True, exist_ok=True)

MODEL = os.environ.get("JARVIS_MODEL") or _config.OLLAMA_MODEL

app = FastAPI(title="JARVIS", version="2.0.0")

_brain_lock = threading.Lock()
_brain = Brain(model=MODEL)
_thoughts: queue.Queue[str] = queue.Queue(maxsize=50)


def _put_thought(s: str) -> None:
    try:
        _thoughts.put_nowait(s)
    except Exception:
        pass


_brain.on_thought = _put_thought


class ChatIn(BaseModel):
    text: str


class SpeakIn(BaseModel):
    text: str
    play_local: bool = True


@app.get("/")
def index():
    f = WEB_DIR / "index.html"
    if f.exists():
        return FileResponse(str(f))
    return JSONResponse({"error": "web/index.html nahi mila. Please web/ directory check karein."})


@app.get("/api/status")
def status() -> dict:
    alive = ollama_alive()
    with _brain_lock:
        brain_model = _brain.model
    return {
        "name": _config.ASSISTANT_NAME,
        "ollama": alive,
        "ollama_host": _config.OLLAMA_HOST,
        "model": brain_model,
        "models": ollama_models() if alive else [],
        "voice": _config.EDGE_VOICE,
        "language": "Hinglish",
        "tools": sorted(_tools.TOOLS.keys()),
        "wake_words": _config.WAKE_WORDS,
        "default_city": _config.DEFAULT_CITY,
    }


@app.post("/api/chat")
def chat(body: ChatIn) -> dict:
    with _brain_lock:
        res = _brain.think(body.text)
    res.setdefault("tools", [])
    if res.get("tool") and res["tool"] not in res["tools"]:
        res["tools"].append(res["tool"])
    return res


@app.get("/api/chat/stream")
def chat_stream(q: str = ""):
    with _thoughts.mutex:
        _thoughts.queue.clear()

    def gen():
        q_text = q
        buf: list[str] = []

        def on_token(ch: str) -> None:
            buf.append(ch)

        def worker() -> dict:
            try:
                with _brain_lock:
                    return _brain.think_stream(q_text, on_token)
            except Exception as e:
                return {"ok": False, "speech": f"Error: {e}", "text": "", "tools": [], "source": "error"}

        result: dict = {}
        th = threading.Thread(target=lambda: result.update(worker()), daemon=True)
        th.start()
        sent = 0

        while th.is_alive():
            if len(buf) > sent:
                chunk = "".join(buf[sent:])
                sent = len(buf)
                yield f"event: token\ndata: {json.dumps({'t': chunk}, ensure_ascii=False)}\n\n"

            try:
                thought = _thoughts.get_nowait()
                yield f"event: thought\ndata: {json.dumps({'t': thought}, ensure_ascii=False)}\n\n"
            except queue.Empty:
                pass

            threading.Event().wait(0.05)

        if len(buf) > sent:
            yield f"event: token\ndata: {json.dumps({'t': ''.join(buf[sent:])}, ensure_ascii=False)}\n\n"

        result.setdefault("tools", [])
        yield f"event: done\ndata: {json.dumps(result, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/api/speak")
def speak(body: SpeakIn):
    """Generate MP3 audio from text using edge-tts with Fast (+35%) Speech Rate."""
    try:
        import asyncio
        import uuid
        import edge_tts

        out = _config.AUDIO_DIR / f"web_{uuid.uuid4().hex[:8]}.mp3"
        voice = _config.EDGE_VOICE

        async def generate_audio() -> None:
            # rate="+35%" se bolne ki speed tez ho gayi hai
            c = edge_tts.Communicate(body.text, voice=voice, rate="+35%")
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

        if body.play_local:
            threading.Thread(target=say, args=(body.text,), daemon=True).start()

        return Response(content=data, media_type="audio/mpeg")
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"{type(e).__name__}: {e}"}, status_code=500)


@app.get("/api/reminders")
def reminders() -> dict:
    try:
        return _tools.run_tool("list_reminders")
    except Exception as e:
        return {"ok": False, "error": str(e)}


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

    try:
        _tools.scheduler.start()
    except Exception:
        pass

    print(f"\n🌐 JARVIS web UI: http://localhost:{port}   (phone: http://<PC-IP>:{port})")
    print(f"🧠 Ollama: {'ONLINE' if ollama_alive() else 'OFFLINE (rule-engine chalega)'}  model={MODEL}\n")
    uvicorn.run(app, host=_config.WEB_HOST, port=port, log_level="warning")


def run_web(port: int | None = None) -> None:
    """Entry point for jarvis-web console script."""
    run(port)


if __name__ == "__main__":
    run()