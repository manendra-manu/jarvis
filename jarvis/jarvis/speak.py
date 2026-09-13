"""
JARVIS - Text to Speech engine with Auto-Cleanup, Fallback & Fast Speech Rate (+35%).
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from jarvis import config as _config

logger = __import__("logging").getLogger("jarvis.speak")


def _clean(text: str) -> str:
    """Clean text by removing links, special formatting, and emojis."""
    t = str(text or "")
    t = re.sub(r"https?://\S+", " link ", t)
    t = re.sub(r"[•\-\*#`>|]", " ", t)
    t = re.sub(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _trim(text: str, limit: int | None = None) -> str:
    """Trim long text cleanly at sentence boundaries."""
    limit = limit or _config.MAX_SPEAK_CHARS
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in (". ", "! ", "? ", ", ", " "):
        if sep in cut[-120:]:
            return cut[:cut.rfind(sep) + 1]
    return cut


def _play_file(path: Path, autodelete: bool = True) -> bool:
    """Play audio file and clean up after playing."""
    p = str(path)
    played = False

    if sys.platform.startswith("win"):
        try:
            from playsound import playsound
            playsound(p)
            played = True
        except Exception:
            pass

        if not played:
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(p)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                pygame.mixer.quit()
                played = True
            except Exception:
                pass

        if not played:
            try:
                subprocess.run(["cmd", "/c", "start", "/min", "", p], check=False)
                time.sleep(2)
                played = True
            except Exception:
                played = False
    else:
        for cmd in (["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", p],
                    ["mpv", "--really-quiet", p], ["afplay", p], ["aplay", p], ["paplay", p]):
            if shutil.which(cmd[0]):
                try:
                    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    played = True
                    break
                except Exception:
                    continue

    if autodelete:
        try:
            if path.exists():
                os.remove(path)
        except Exception:
            pass

    return played


def _speak_edge(text: str, voice: str | None = None) -> bool:
    """Edge TTS Engine (High Quality Online Voice with +35% Speed)"""
    try:
        import asyncio
        import edge_tts

        voice_name = voice or _config.EDGE_VOICE
        out = _config.AUDIO_DIR / f"j_{uuid.uuid4().hex[:8]}.mp3"

        async def run() -> None:
            c = edge_tts.Communicate(text, voice=voice_name, rate="+35%")
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
                        new_loop.run_until_complete(run())
                    finally:
                        new_loop.close()
                pool.submit(runner).result()
        else:
            asyncio.run(run())

        return _play_file(out)
    except Exception as e:
        logger.debug("Edge TTS failed: %s", e)
        return False


def _speak_gtts(text: str, voice: str | None = None) -> bool:
    """Google TTS Engine"""
    try:
        from gtts import gTTS
        out = _config.AUDIO_DIR / f"j_{uuid.uuid4().hex[:8]}.mp3"
        gTTS(text=text, lang=_config.GTTS_LANG, slow=False).save(str(out))
        return _play_file(out)
    except Exception:
        return False


def _speak_piper(text: str, voice: str | None = None) -> bool:
    """Piper Offline TTS Engine"""
    try:
        model = _config.PIPER_VOICE_PATH
        if not model:
            cand = list(Path(_config.BASE_DIR).glob("**/*.onnx")) + list(Path.home().glob("piper/*.onnx"))
            model = str(cand[0]) if cand else ""
        if not model or not shutil.which("piper"):
            return False
        out = _config.AUDIO_DIR / f"j_{uuid.uuid4().hex[:8]}.wav"
        subprocess.run(["piper", "--model", model, "--output_file", str(out), text],
                       check=True, capture_output=True)
        return _play_file(out)
    except Exception:
        return False


def _speak_sapi(text: str, voice: str | None = None) -> bool:
    """Windows SAPI5 Offline Engine"""
    if not sys.platform.startswith("win"):
        return False
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        for v in speaker.GetVoices():
            desc = v.GetDescription()
            if "Hindi" in desc or "Heera" in desc or "Kalpana" in desc:
                speaker.Voice = v
                break
        speaker.Rate = 2
        speaker.Speak(text)
        return True
    except Exception:
        pass

    try:
        safe = text.replace('"', '`"').replace("'", "''")
        cmd = f'Add-Type -AssemblyName System.Speech; $syn = New-Object System.Speech.Synthesis.SpeechSynthesizer; $syn.Rate = 2; $syn.Speak("{safe}")'
        subprocess.run(["powershell", "-Command", cmd], check=False, capture_output=True)
        return True
    except Exception:
        return False


_ENGINES = {
    "edge": _speak_edge,
    "gTTS": _speak_gtts,
    "piper": _speak_piper,
    "say": _speak_sapi
}


class Speaker:
    """JARVIS TTS Engine with Fallback & Thread Management."""

    def __init__(self, engines: list | None = None, voice: str | None = None,
                 muted: bool = False, queue: bool = True) -> None:
        self.engines = engines or list(_config.TTS_ENGINES)
        self.voice = voice or _config.EDGE_VOICE
        self.muted = muted
        self.queue = queue
        self._thread: threading.Thread | None = None
        self.active: str | None = None
        self.on_speak = None
        logger.info("Speaker initialized with engines: %s", self.engines)

    def available(self) -> list:
        out = []
        if "edge" in self.engines:
            try:
                import edge_tts
                out.append("edge")
            except Exception:
                pass

        if "gTTS" in self.engines:
            try:
                import gtts
                out.append("gTTS")
            except Exception:
                pass

        if "piper" in self.engines and (_config.PIPER_VOICE_PATH or shutil.which("piper")):
            out.append("piper")

        if "say" in self.engines and sys.platform.startswith("win"):
            out.append("say")

        return out

    def say(self, text: str, block: bool | None = None) -> str:
        """Speak text. block=True -> Wait; False -> Background Thread."""
        text = _trim(_clean(text))
        if not text or self.muted:
            return ""

        if self.on_speak:
            try:
                self.on_speak(text)
            except Exception:
                pass

        if self.queue and self._thread and self._thread.is_alive():
            self._thread.join()

        if block is None:
            block = not self.queue

        if block:
            self._do_say(text)
        else:
            self._thread = threading.Thread(target=self._do_say, args=(text,), daemon=True)
            self._thread.start()

        return text

    def _do_say(self, text: str) -> None:
        for name in self.engines:
            fn = _ENGINES.get(name)
            if not fn:
                continue

            try:
                if fn(text, voice=self.voice):
                    self.active = name
                    logger.info("TTS spoken via %s", name)
                    return
            except Exception as e:
                logger.debug("TTS %s failed: %s", name, e)

        logger.warning("No TTS engine worked.")
        print("[TTS] Koi voice engine nahi chala. Check audio settings.")

    def speak_async(self, text: str) -> str:
        return self.say(text, block=False)

    def wait(self) -> None:
        if self._thread and self._thread.is_alive():
            self._thread.join()

    def stop(self) -> None:
        if sys.platform.startswith("win"):
            subprocess.run(["taskkill", "/F", "/IM", "wmplayer.exe"], capture_output=True, check=False)
        else:
            for p in ("ffplay", "mpv", "aplay", "paplay"):
                if shutil.which(p):
                    subprocess.run(["pkill", "-f", p], capture_output=True, check=False)


def say(text: str, **kw) -> str:
    """One-shot shortcut: say('Namaste')"""
    return Speaker(**kw).say(text, block=True)


if __name__ == "__main__":
    msg = " ".join(sys.argv[1:]) or "Namaste! Main JARVIS hoon. Awaaz test ho raha hai."
    spk = Speaker()
    print("Available engines:", spk.available())
    spk.say(msg, block=True)