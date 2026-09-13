#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
  GROQ CLOUD BRAIN - SETUP (2 minute)
============================================================
Bas ye script chalao (setup-cloud.bat se khud chal jaata hai):
  1) Browser apne aap khulega -> console.groq.com/keys
  2) Google se sign-in karo -> "Create API Key" -> key copy
  3) Yahan paste karo -> Enter
  4) Script khud dekhti hai kaunsa model aapke plan pe chalta hai,
     khud test karti hai aur config.py mein save kar deti hai
  5) Ab run-jarvis.bat chalao - smart jawab 1-2 sec mein!

Bina credit card. Bilkul free. Kabhi bhi delete kar sakte ho.
============================================================
"""
import pathlib
import re
import sys
import time
import webbrowser

try:
    import requests
except ImportError:
    sys.exit("requests package nahi mila. Pehle ye chalao:  pip install requests")

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402

KEYS_PAGE = "https://console.groq.com/keys"
MODELS_URL = "https://api.groq.com/openai/v1/models"

# Tarjeeh (preference) - jo pehla aapke plan pe milega wahi lagega
PREFERRED_MODELS = [
    "openai/gpt-oss-20b",              # 1000 tok/s - bijli jaisa tez
    "openai/gpt-oss-120b",             # 500 tok/s - sabse smart
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "groq/compound-mini",
    "qwen3-32b",
    "kimi-k2-instruct",
]


def available_models(key: str) -> list:
    """Aapki key se poochho: Groq pe kaunse models chalu hain."""
    try:
        r = requests.get(MODELS_URL, headers={"Authorization": f"Bearer {key}"}, timeout=20)
        if r.status_code == 200:
            return [m.get("id", "") for m in r.json().get("data", [])]
    except requests.exceptions.RequestException:
        pass
    return []


def pick_model(key: str):
    """Aapke plan pe chalne wala best model chuno."""
    avail = available_models(key)
    for m in PREFERRED_MODELS:
        if m in avail:
            return m, avail
    # preference mein nahi mila -> pehla chat-model jo audio/safety wala na ho
    for m in avail:
        if not any(x in m for x in ("whisper", "prompt-guard", "orpheus", "safeguard")):
            return m, avail
    return None, avail


def test_key(key: str, model: str):
    """Groq pe ek chhota sa test message bhejo. (status_code, detail)"""
    try:
        r = requests.post(
            config.GROQ_URL,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": model, "max_tokens": 10,
                  "messages": [{"role": "user", "content": "Namaste"}]},
            timeout=30,
        )
        return r.status_code, r.text[:200]
    except requests.exceptions.RequestException as e:
        return None, str(e)


def save_key(key: str, model: str) -> None:
    p = HERE / "config.py"
    s = p.read_text(encoding="utf-8")
    s = re.sub(r'GROQ_API_KEY = "[^"]*"', f'GROQ_API_KEY = "{key}"', s)
    s = re.sub(r'GROQ_MODEL = "[^"]*"', f'GROQ_MODEL = "{model}"', s)
    p.write_text(s, encoding="utf-8")


def main():
    print()
    print("=" * 56)
    print("   GROQ CLOUD BRAIN SETUP  -  free, bina card")
    print("=" * 56)
    print()
    print("Browser khol raha hoon: " + KEYS_PAGE)
    print("Wahan:  Google se sign-in  ->  'Create API Key'  ->  copy")
    print("(key gsk_ se shuru hoti hai)")
    print()
    try:
        webbrowser.open(KEYS_PAGE)
    except Exception:
        print("Browser nahi khula? Khud khol lo: " + KEYS_PAGE)

    while True:
        try:
            key = input(">>> Key yahan PASTE karo (right-click) aur Enter dabao: ").strip().strip('"').strip("'")
        except (EOFError, KeyboardInterrupt):
            print("\nCancel kar diya. Phir se chalana ho to setup-cloud.bat double-click karo.")
            return
        if not key:
            print("Khali hai - key copy karke paste karo.")
            continue
        if not key.startswith("gsk_"):
            print("Hmm, Groq ki key 'gsk_' se shuru hoti hai. Paste sahi hua?")
        print("Key test kar rahi hoon... (2-3 sec)")

        code, detail = test_key(key, PREFERRED_MODELS[0])
        if code == 401:
            print("❌ Key galat/purani lagi. Groq page se naya 'Create API Key' karke dobara paste karo.")
            continue
        if code is None:
            print("❌ Internet se connect nahi ho paya. Net check karke dobara chalao.")
            print(f"   Detail: {detail}")
            continue

        # key valid hai -> ab aapke plan pe chalne wala model chuno
        print("✅ Key sahi hai! Ab aapke plan ke models dekh rahi hoon...")
        model, avail = pick_model(key)
        if not model:
            print("❌ Aapke Groq plan pe koi chat-model nahi mila.")
            print(f"   Mile models: {avail or '(kuch nahi)'}")
            continue
        print(f"   Model mila: {model}")
        code, detail = test_key(key, model)
        if code != 200:
            print(f"❌ {model} se test fail (code {code}).")
            print(f"   Detail: {detail}")
            continue

        save_key(key, model)
        print()
        print("=" * 56)
        print(f"   🎉 KEY + MODEL KAAM KAR RAHE HAIN!  ({model})")
        print("=" * 56)
        print()
        print("  config.py mein save ho gaya.")
        print("  Ab run-jarvis.bat chalao - banner mein ye dikhega:")
        print(f"  ☁️  Cloud brain: ON (Groq {model}) - smart jawab 1-2 sec")
        print()
        time.sleep(1)
        return


if __name__ == "__main__":
    main()
