"""
JARVIS ke KAAN - Speech to Text (mic se sun'na).
"""
from __future__ import annotations

import glob
import logging
import time
from pathlib import Path
from typing import Callable

from jarvis import config as _config

logger = logging.getLogger("jarvis.listen")

SAMPLE_RATE = 16000


class NoMicError(Exception):
    """Koi mic backend installed nahi hai."""


class Listener:
    def __init__(self, engine: str | None = None, language: str | None = None,
                 wake_words: list | None = None) -> None:
        self.engine = engine or _config.STT_ENGINE
        self.language = language or _config.STT_LANGUAGE
        self.wake_words = [w.lower() for w in (wake_words or _config.WAKE_WORDS)]
        self._backend: str | None = None
        self._sr = None
        self._vosk_model = None
        self.on_heard: Callable[[str], None] | None = None

    def backend_name(self) -> str:
        if self._backend is None:
            try:
                import sounddevice as sd
                sd.query_devices()
                self._backend = "sounddevice"
            except Exception:
                try:
                    import speech_recognition as sr
                    self._backend = "pyaudio"
                except Exception:
                    self._backend = "none"
        return self._backend

    @staticmethod
    def list_microphones() -> list:
        try:
            import sounddevice as sd
            devs = sd.query_devices()
            return [d["name"] for d in devs if d.get("max_input_channels", 0) > 0]
        except Exception:
            pass
        try:
            import speech_recognition as sr
            return sr.Microphone.list_microphone_names()
        except Exception as e:
            return [f"(mic list nahi mili: {e})"]

    def _record_sd(self, timeout: int, phrase_limit: int) -> bytes | None:
        import sounddevice as sd
        import numpy as np

        chunk = int(SAMPLE_RATE * 0.25)
        frames: list[bytes] = []
        speech_seen = False
        silence_after = 0.0
        waited = 0.0
        rms_base = None

        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                                dtype="int16", blocksize=chunk) as stream:
                while waited < timeout + phrase_limit:
                    data, _ = stream.read(chunk)
                    waited += 0.25
                    arr = np.frombuffer(data, dtype=np.int16)
                    rms = float(np.sqrt(np.mean(arr.astype(np.float64) ** 2)))

                    if rms_base is None:
                        rms_base = rms
                        continue

                    rms_base = max(rms_base * 0.995 + rms * 0.005, 30.0)
                    loud = rms > max(rms_base * 2.5, 400.0)

                    if loud:
                        speech_seen = True
                        silence_after = 0.0
                    elif speech_seen:
                        silence_after += 0.25

                    if speech_seen or waited > timeout * 0.4:
                        frames.append(bytes(data))

                    if speech_seen and silence_after >= 0.9:
                        break

                    if not speech_seen and waited > timeout:
                        break
        except Exception as e:
            logger.error("Sounddevice recording error: %s", e)
            return None

        if not frames or not speech_seen:
            return None
        return b"".join(frames)

    def _record_pyaudio(self, timeout: int, phrase_limit: int) -> bytes | None:
        import speech_recognition as sr
        r = sr.Recognizer()
        r.energy_threshold = 300
        r.dynamic_energy_threshold = True
        r.pause_threshold = 0.8

        try:
            with sr.Microphone() as source:
                try:
                    r.adjust_for_ambient_noise(source, duration=0.6)
                except Exception:
                    pass
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                return audio.get_wav_data() if hasattr(audio, "get_wav_data") else audio.frame_data
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            logger.error("PyAudio recording error: %s", e)
            return None

    def record(self, timeout: int | None = None, phrase_limit: int | None = None) -> bytes | None:
        timeout = timeout or _config.LISTEN_TIMEOUT
        phrase_limit = phrase_limit or _config.PHRASE_LIMIT
        backend = self.backend_name()

        if backend == "none":
            raise NoMicError("Mic ka koi driver installed nahi hai. Run: pip install sounddevice numpy")

        if backend == "sounddevice":
            return self._record_sd(timeout, phrase_limit)
        return self._record_pyaudio(timeout, phrase_limit)

    def listen_once(self, timeout: int | None = None, phrase_limit: int | None = None) -> str:
        pcm = self.record(timeout, phrase_limit)
        if pcm is None:
            return ""

        if self.engine == "vosk":
            text = self._recognize_vosk(pcm)
        else:
            text = self._recognize_google(pcm)

        text = text.strip()
        if text and self.on_heard:
            try:
                self.on_heard(text)
            except Exception:
                pass

        return text

    def _recognize_google(self, pcm: bytes) -> str:
        import speech_recognition as sr
        audio = sr.AudioData(pcm, SAMPLE_RATE, 2)
        try:
            return sr.Recognizer().recognize_google(audio, language=self.language)
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            logger.error("Google STT error: %s", e)
            print(f"[STT] Google API error (internet check karo): {e}")
            return ""

    def _recognize_vosk(self, pcm: bytes) -> str:
        from vosk import Model, KaldiRecognizer, SetLogLevel
        import json as _json

        if self._vosk_model is None:
            SetLogLevel(-1)
            paths = (glob.glob(str(Path(_config.BASE_DIR) / "models" / "vosk-*"))
                     + glob.glob(str(Path.home() / "vosk-*")) + glob.glob("vosk-*"))
            if not paths:
                raise FileNotFoundError(
                    "Vosk model nahi mila. 'vosk-model-small-hi-0.4' download karke jarvis/models/ mein daalo.")
            self._vosk_model = Model(paths[0])

        rec = KaldiRecognizer(self._vosk_model, SAMPLE_RATE)
        text = ""
        for i in range(0, len(pcm), 4000):
            if rec.AcceptWaveform(pcm[i:i + 4000]):
                text += " " + _json.loads(rec.Result()).get("text", "")
        text += " " + _json.loads(rec.FinalResult()).get("text", "")
        return text.strip()

    def listen_for_wake_word(self, on_wake: Callable[[], None] | None = None,
                             stop_flag: Callable[[], bool] | None = None) -> None:
        stop_flag = stop_flag or (lambda: False)
        if self.backend_name() == "none":
            raise NoMicError("pip install sounddevice numpy")

        logger.info("Listening for wake word: %s", self.wake_words)
        print(f"🎤 Sun rahi hoon... bolo: {', '.join(self.wake_words)}  (Ctrl+C = band)")

        # 1. OpenWakeWord Model Try Karein
        try:
            from openwakeword.model import Model as OWW
            import numpy as np
            import sounddevice as sd

            oww = OWW(wakeword_models=["hey_jarvis"], inference_framework="onnx")

            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                                blocksize=1280) as stream:
                while not stop_flag():
                    data, _ = stream.read(1280)
                    preds = oww.predict(np.frombuffer(data, dtype=np.int16))  # Fixed oow -> oww
                    if any(v > 0.5 for v in preds.values()):
                        oww.reset()  # Fixed oow -> oww
                        if on_wake:
                            on_wake()
            return
        except NoMicError:
            raise
        except ImportError:
            logger.info("openwakeword not installed - fallback keyword mode")
            print("[WAKE] openwakeword nahi hai - keyword mode chal raha hai.")
        except Exception as e:
            logger.warning("Wake-word model failed: %s", e)
            print(f"[WAKE] wake-word model nahi chala ({type(e).__name__}) - fallback keyword mode.")

        # 2. Fallback Speech Recognition Loop
        while not stop_flag():
            heard = self.listen_once(timeout=8, phrase_limit=3)
            if heard:
                if any(w in heard.lower() for w in self.wake_words):
                    if on_wake:
                        on_wake()
            else:
                time.sleep(0.1)  # CPU Protection if empty audio


if __name__ == "__main__":
    print("Backend:", Listener().backend_name())
    print("Mics:", Listener.list_microphones())
    l = Listener()
    print("Boliye...", flush=True)
    print("Aapne kaha:", l.listen_once())