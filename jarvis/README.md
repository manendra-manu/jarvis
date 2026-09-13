# 🤖 J.A.R.V.I.S — Aapka Personal Voice Assistant (Hinglish)

Ek **asli, chalane layak** voice agent — JARVIS jaisa bolne wala software.
Hindi + English (Hinglish) samajhta hai, **female awaaz** mein jawab deta hai,
aur aapke computer par asli kaam karta hai (reminder, files, apps, hisaab, mausam, WhatsApp…).

**Do tariko se chalta hai:**
- 🖥️ **Desktop app** — `python jarvis.py` (mic se baat karo, "Hey JARVIS" bolo)
- 🌐 **Web app** — `python jarvis.py --web` (browser se, phone se bhi)

**AI dimaag:** Ollama (100% free + offline). Ollama band ho tab bhi **rule engine**
se basic saare commands chalte rehte hain.

---

## ⚡ 3 step mein shuru (Windows)

> 📖 **Pehli baar install kar rahe ho?** → **`SETUP-GUIDE.md`** kholo.
> Usme har step screenshot-jaisa samjhaya gaya hai (PATH tick, mic permission, errors ka ilaaj).

| Step | Kya karna hai |
|---|---|
| **1** | **Python install karo** → https://www.python.org/downloads/ <br>⚠️ Install ke waqt **"Add python.exe to PATH"** tick karna **zaroori** hai <br>⚠️ **Python 3.10 ya naya** chahiye |
| **2** | Is `jarvis` folder mein **`install.bat`** par **double click** karo (3–5 min) |
| **3** | **`run-jarvis.bat`** double click → boliye *"kitne baje hain"* 🎤 |

Kuch gadbad ho to → **`check.bat`** chalao, wo khud bata dega kya missing hai.

Browser wala JARVIS chahiye? → **`run-web.bat`** → http://localhost:8000 khul jayega.

`.exe` banana ho (bina Python ke chalane layak): **`build-exe.bat`** → `dist\JARVIS.exe`

---

## 🧠 Full brain ke liye Ollama (recommended, free)

Bina Ollama ke basic commands chalte hain. **Smart jawab** chahiye to:

```bat
:: 1) Ollama install karo
start https://ollama.com/download

:: 2) model download karo (ek baar)
ollama pull llama3.1:8b      :: 4.9 GB - sabse balanced
:: PC kamzor ho (4GB RAM) to:
ollama pull llama3.2:3b      :: 2 GB - halka aur fast

:: 3) Ollama chalu rakho (background mein chalta hai), phir JARVIS chalao
run-jarvis.bat
```

Dusra model use karna ho:
```bat
python jarvis.py --model qwen2.5:7b
python jarvis.py --model mistral
```
Model `config.py` mein `OLLAMA_MODEL` se bhi badal sakte ho.

---

## 🎤 Aap ye bol sakte ho (tested ✅)

### ⏰ Time & Reminder
```
kitne baje hain
aaj ki date kya hai
10 minute baad paani peene ka reminder laga
shaam 6 baje meeting ka reminder
kal subah 9 baje gym ka reminder laga
kaunse reminder hain
saare reminder delete karo
```

### 🧮 Hisaab
```
250 guna 4 plus 15 kitna hota hai
100 ka 15 percent
144 ka square root
```

### 📝 Notes
```
note karo doodh lana hai
mere notes dikha
```

### 🌤 Mausam & Jankari
```
jabalpur ka mausam kaisa hai
weather in bhopal
virat kohli kaun hai
taj mahal ke baare mein bata
python search karo
```

### 💻 Computer control (Windows)
```
notepad kholo
calculator chalao
google.com kholo
arijit singh ka gaana chalao
spotify pe tum hi ho chalao
resume file dhoondho
volume up / volume down / mute
system info        (battery, CPU, RAM)
screenshot lo
shutdown karo      (30 second ka time milta hai)
cancel shutdown
```

### 💬 Message
```
whatsapp bhej 9876543210 main aa raha hoon
email bhej ravi@gmail.com meeting kal hai
```

### 😄 Aur bhi
```
ek joke sunao
tum kaun ho
bye
```

> Naya command add karna hai? `rules.py` kholo aur ek `if re.search(...)` block daal do.
> Naya tool add karna hai? `tools.py` mein function banao + `TOOLS` aur `TOOL_SCHEMAS` mein naam daal do.

---

## 🗣 Awaaz (TTS) — female Hindi voice

`config.py` mein `EDGE_VOICE` set hai: **`hi-IN-SwaraNeural`** (Microsoft ki free neural voice).

Priority order (jo pehle available milega wahi chalega):

| Engine | Kya hai | Internet | Quality |
|---|---|---|---|
| `edge` | Microsoft neural (**default**) | chahiye | ⭐⭐⭐⭐⭐ |
| `gTTS` | Google TTS | chahiye | ⭐⭐⭐⭐ |
| `piper` | Offline, fast | **nahi chahiye** | ⭐⭐⭐⭐ |
| `say` | Windows built-in | **nahi chahiye** | ⭐⭐ |

**Dusri female voices** (`config.py` → `EDGE_VOICE`):
- `hi-IN-SwaraNeural` — natural female ✅ default
- `hi-IN-AnanyaNeural` — dusri female
- `en-IN-NeerjaNeural` — Indian English female
- `en-US-AriaNeural` — American female

**100% offline awaaz (Piper):**
```bat
pip install piper-tts
:: Hindi model download karo (huggingface: rhasspy/piper-voices -> hi/hi_IN/pratham/medium)
:: .onnx file ka path config.py mein PIPER_VOICE_PATH mein daalo
```

---

## 🎙 Mic (STT) — sun'na

Mic ke liye **`sounddevice`** use hota hai — PortAudio bundled aata hai, isliye
**koi C++ build nahi chahiye** aur ye har Python (3.10–3.14+) pe chalta hai.
Agar kuch atke to: `pip install sounddevice numpy`

`config.py` → `STT_ENGINE`:
- `"google"` — free, internet chahiye, Hindi+English dono (**default**)
- `"vosk"` — **100% offline**. Model: https://alphacephei.com/vosk/models → `vosk-model-small-hi-0.4`
  download karke `jarvis/models/` folder mein daalo.

**Wake word** ("Hey JARVIS" bolne pe activate):
```bat
pip install openwakeword
python -c "import openwakeword; openwakeword.utils.download_models(['hey_jarvis'])"
```
Wake word band karna ho → `python jarvis.py --nowake` (har baar sunega).

---

## 🖥 Chalane ke saare tarike

```bat
python jarvis.py                  :: "Hey JARVIS" bolo, phir command
python jarvis.py --nowake         :: har baar sune (wake word nahi)
python jarvis.py --text           :: type karke baat karo (mic test)
python jarvis.py --mute           :: awaaz band, sirf text
python jarvis.py --web            :: browser wala JARVIS (http://localhost:8000)
python jarvis.py --model llama3.2:3b
python jarvis.py --voice hi-IN-AnanyaNeural
```

**Phone se web JARVIS:** PC aur phone ek hi WiFi pe hon, phir phone mein
`http://<PC-ka-IP>:8000` kholo (IP ke liye `ipconfig` chalao).
> 📱 Phone ke mic ke liye **HTTPS** chahiye. Local pe `ngrok http 8000` ya
> `python -m http.server` + self-signed cert se ho jayega. Warna type karke baat karo.

---

## 📁 Folder structure

```
jarvis/
├── jarvis.py          ← MAIN app (desktop + CLI)
├── webapp.py          ← FastAPI web server
├── brain.py           ← dimaag: rule engine + Ollama + tool calling
├── rules.py           ← offline Hinglish command parser
├── tools.py           ← 24 asli kaam (reminder, files, weather, whatsapp…)
├── speak.py           ← TTS (bolna) — edge/gTTS/piper/Windows
├── listen.py          ← STT (sun'na) — Google/Vosk + wake word
├── config.py          ← ⚙️ SAARI settings yahan
├── requirements.txt          ← zaroori packages
├── requirements-optional.txt ← optional (offline voice, wake word, WhatsApp)
├── SETUP-GUIDE.md     ← 📖 pehle ye padho (step-by-step)
├── install.bat        ← setup (ek baar)
├── run-jarvis.bat     ← voice assistant chalao
├── run-web.bat        ← browser wala JARVIS
├── check.bat/check.py ← 🩺 health check (kya ready hai)
├── build-exe.bat      ← .exe banao
├── web/index.html     ← browser UI (arc-reactor orb, mic, live stream)
├── tests/test_jarvis.py   ← 70 tests
├── data/              ← reminders.json, notes.txt, history.jsonl, audio/
└── demo/              ← JARVIS ki awaaz ke sample MP3
```

---

## ✅ Tests

```bat
python -m unittest discover -s tests -v
python check.py          :: kya-kya installed hai, ye bhi batata hai
```
70 tests — tools, rule engine, Ollama tool-calling flow, speaker, aur web API sab cover karte hain.
(Mic ya speaker ki zaroorat nahi.)

---

## 🔧 Common problems

| Problem | Solution |
|---|---|
| `python nahi mila` | Python install karo, **"Add to PATH" tick** karo, PC restart karo |
| mic/pyaudio problem | Ab sounddevice use hota hai: `pip install sounddevice numpy` |
| Mic nahi chal raha | Windows Settings → Privacy → Microphone → **desktop apps ko allow** karo |
| Koi awaaz nahi | `pip install edge-tts gTTS playsound` ; ya `--voice` badal ke dekho |
| `Ollama OFFLINE` dikh raha | Ollama app chalu karo, phir `ollama list` se check karo |
| Jawab bahut slow | Halka model lo: `--model llama3.2:3b` |
| Reminder nahi baja | JARVIS **chalu** hona chahiye (band karoge to restart pe bacha hua reminder chalega) |
| Web UI khul nahi raha | `python jarvis.py --web` chalao, phir http://localhost:8000 |

---

## 🔐 Security note

`system_control` (shutdown/restart) aur `open_app` aapke PC par asli command chalate hain —
shutdown se pehle **30 second** ka time milta hai, `cancel shutdown` bolo to ruk jayega.
Ollama sab kuch **local** chalata hai, aapki baatein kahin bhejta nahi (Google STT aur
edge-tts internet use karte hain — fully offline chahiye to `vosk` + `piper` use karo).

---

## 🚀 Aage kya add kar sakte ho

- 📅 Google Calendar / Todoist sync
- 📧 Gmail actually bhejna (SMTP)
- 🏠 Smart home (Home Assistant)
- 🎬 Netflix/Prime control
- 📱 Telegram bot se door se command
- 🧠 Memory (long-term) — ChromaDB se

`tools.py` mein ek function + `TOOL_SCHEMAS` mein ek entry = JARVIS ko naya kaam aa gaya. 🎯
