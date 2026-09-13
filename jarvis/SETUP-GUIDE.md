# 🚀 JARVIS — Setup Guide (Windows, bilkul step-by-step)

Ye guide padh ke aap **15 minute** mein JARVIS chala loge. Har step mein likha hai
ki screen par **kya dikhna chahiye** — taaki pata chale sahi ja raha hai ya nahi.

> 📌 Sab kuch `jarvis` folder ke andar hi hona chahiye. Folder ko kahin bhi rakh sakte ho
> (Desktop sabse aasan hai).

---

## 📦 STEP 0 — File nikalo (extract karo)

1. Download ki hui **`jarvis.zip`** file par **right click** karo
2. **"Extract All…"** dabaao → **Extract** dabaao
3. Ab aapke paas ek **`jarvis`** folder hoga

✅ **Check:** folder kholo — andar `jarvis.py`, `install.bat`, `run-jarvis.bat`,
`web` folder, `tools.py` dikhna chahiye.

> ⚠️ **Zaroori:** zip ke andar sirf `jarvis` folder ho. Agar kholne par seedha
> `jarvis.py` dikhe (bina folder ke) to bhi theek hai — bas yaad rakho ki
> `install.bat` usi folder mein hona chahiye jahan `requirements.txt` hai.

---

## 🐍 STEP 1 — Python install karo (5 min, sirf ek baar)

1. Browser mein kholo: **https://www.python.org/downloads/**
2. Bada yellow button **"Download Python 3.13.x"** dabaao
3. Downloaded file chalao. **Sabse zaroori screen:**

   ```
   ┌─────────────────────────────────────────────┐
   │  Install Python 3.13.x                      │
   │                                             │
   │  ☑ Use admin privileges ...                 │
   │  ☑ Add python.exe to PATH   ← YE TICK KARO! │  ⬅⬅⬅
   │                                             │
   │      [ Install Now ]        ← ye dabaao     │
   └─────────────────────────────────────────────┘
   ```

   > 🚨 **"Add python.exe to PATH" tick kiye bina install kiya to JARVIS chalega hi nahi.**
   > Bhool gaye? Koi baat nahi — Python dobara install karo aur **"Modify"** chuno.

4. Install ho jaye to **PC restart** kar lo (safe rahega)

✅ **Check:** `Windows key` dabaao → `cmd` likho → Enter. Black window mein likho:
```
python --version
```
Dikhna chahiye: `Python 3.13.x` (ya 3.10 se upar kuch bhi).

> ❌ Agar `'python' is not recognized` aaye → PATH tick nahi hua tha, Python dobara install karo.

---

## ⚙️ STEP 2 — JARVIS install karo (3–5 min, sirf ek baar)

1. `jarvis` folder kholo
2. **`install.bat`** par **double click** karo

   > Agar Windows ne roka ("Windows protected your PC"):
   > **More info** → **Run anyway** dabaao.

3. Ek black window khulegi, packages install honge. **2–5 minute** lagega, internet chahiye.

✅ **Screen par ye dikhna chahiye:**
```
  [1/6] Python mil gaya:  Python 3.13.1
  [2/6] Python version theek hai (3.10+)
  [3/6] Zaroori packages install ho rahe hain...
  [4/6] Optional packages ...  (fail ho to bhi chalega)
  [5/6] Data folders ...  OK
  [6/6] Test chal rahe hain...
  ....................................................
  Ran 70 tests in 3s
  OK
  ==========================================================
     SETUP POORA!
```

> 🟢 **`Ran 70 tests ... OK`** dikhe = sab perfect hai.
> `(skipped=1)` dikhe to bas ye chalao: `pip install httpx` — phir sab 70 chalenge.

### Agar install mein error aaye

| Error | Solution |
|---|---|
| mic nahi chal raha / `pyaudio` fail | Ab JARVIS **sounddevice** use karta hai (koi build nahi chahiye):<br>`pip install sounddevice numpy` |
| `Microsoft Visual C++ 14.0 required` | Ye link install karo: https://aka.ms/vs/17/release/vs_BuildTools.exe |
| Internet/timeout error | Dobara `install.bat` chalao (ruk-ruk ke chalta hai) |
| `permission denied` | `install.bat` par right click → **Run as administrator** |

---

## 🎤 STEP 3 — JARVIS chalao!

### Tarika A — Voice assistant (mic se baat)
**`run-jarvis.bat`** par double click karo.

✅ Screen par ye dikhna chahiye:
```
     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
     ...
  🧠 Ollama: OFFLINE  -> basic commands bina AI ke bhi chalenge
  🔊 Awaaz: edge, gTTS
  🎤 Microphones: ['Microphone Array (Realtek...)']
```
Phir JARVIS bolega: *"Namaste! Main JARVIS hoon…"*

Ab boliye: **"kitne baje hain"** 🎉

> 🎙️ Pehli baar Windows poochega **"Microphone access"** → **Allow** karo.
> Settings → Privacy → Microphone → *"Allow desktop apps to access your microphone"* **ON** karo.

### Tarika B — Browser wala JARVIS
**`run-web.bat`** par double click → browser mein http://localhost:8000 khul jayega.
Neeche **mic button** dabaao aur bolo.

> 📱 **Phone se** chalana ho: PC aur phone ek hi WiFi pe hon →
> PC pe CMD mein `ipconfig` chalao → `IPv4 Address` dekho (jaise `192.168.1.5`) →
> phone ke browser mein `http://192.168.1.5:8000` kholo.

### Tarika C — Pehle type karke test karo (mic ke bina)
```
python jarvis.py --text
```
Likho: `kitne baje hain` → Enter

---

## 🧠 STEP 4 — Smart brain (Ollama) — recommended, FREE

Abhi JARVIS **basic commands** samajhta hai (time, reminder, hisaab, app, mausam…).
**Khul kar baat** karne ke liye Ollama chahiye:

1. Kholo: **https://ollama.com/download** → Windows wala download → install
2. Install ke baad Ollama background mein chalنے lagta hai (taskbar mein icon)
3. **CMD** kholo aur likho:
   ```
   ollama pull llama3.1:8b
   ```
   (4.9 GB download hoga, internet speed pe depend karta hai)

   > 💻 PC kamzor hai (4 GB RAM)? Halka model lo:
   > ```
   > ollama pull llama3.2:3b
   > ```
   > phir chalao: `python jarvis.py --model llama3.2:3b`

4. Ab `run-jarvis.bat` chalao — screen par dikhega:
   ```
   🧠 Ollama: ONLINE   models: llama3.1:8b
   ```

✅ Ab aap kuch bhi pooch sakte ho: *"resume kaise banate hain"*, *"mera mood off hai"*,
*"Python mein list aur tuple mein kya farq hai"* — JARVIS tools use karke jawab dega.

---

## 🩺 Kuch bhi gadbad? — `check.bat` chalao

**`check.bat`** par double click karo. Ye khud bata dega kya ready hai:

```
  [OK] Python                : 3.13.1
  [OK] requests              : installed
  [XX] microphone driver     : pip install pipwin && pipwin install pyaudio
  [!!] Ollama (AI dimaag)    : BAND - basic commands phir bhi chalenge
  [OK] Tools                 : 24 tools ready, 24 AI schemas
  [OK] Tests                 : Ran 70 tests ... OK

  SAB READY HAI!  Ab chalao: run-jarvis.bat
```

**`[OK]` = ready · `[!!]` = optional · `[XX]` = theek karna zaroori**

---

## 🔊 Awaaz badalni ho? (female/male, Hindi/English)

`config.py` file **Notepad** mein kholo, ye line dhundo:
```python
EDGE_VOICE = "hi-IN-SwaraNeural"
```

| Voice | Kaisi hai |
|---|---|
| `hi-IN-SwaraNeural` | Hindi female, natural ✅ **default** |
| `hi-IN-AnanyaNeural` | Hindi female, dusri awaaz |
| `en-IN-NeerjaNeural` | Indian English female |
| `en-IN-PrabhatNeural` | Indian English **male** |
| `en-US-AriaNeural` | American female |
| `en-GB-SoniaNeural` | British female |

Save karo (Ctrl+S) → JARVIS dobara chalao.

**Bolne ki speed:** `SPEECH_RATE_WPM = 175` → 150 = dheere, 200 = tez.

---

## 📋 Roz ke liye shortcut

1. `jarvis` folder kholo
2. `run-jarvis.bat` par **right click** → **"Send to" → "Desktop (create shortcut)"**
3. Ab Desktop se ek click mein JARVIS chalu! 🎯

---

## ❓ Sabse common sawaal

**Q: Kya internet zaroori hai?**
A: Basic commands ke liye **nahi** (Ollama offline chalta hai). Par awaaz (edge-tts) aur
mausam/search ke liye internet chahiye. **100% offline** chahiye to `piper` (awaaz) +
`vosk` (sun'na) install karo — README mein tarika hai.

**Q: Reminder tab bajega jab JARVIS band ho?**
A: Reminder **file mein save** rehta hai. JARVIS dobara chalu karoge to bacha hua reminder
turant chalega. Chalu rehna chahiye time pe bajne ke liye.

**Q: Kitna RAM/disk chahiye?**
A: JARVIS khud: ~200 MB. Ollama ke saath: `llama3.2:3b` = 2 GB (4 GB RAM wale PC pe chalega),
`llama3.1:8b` = 4.9 GB (8 GB RAM chahiye).

**Q: Kya meri baatein kahin jaati hain?**
A: Ollama **poora local** hai — kuch bhi bahar nahi jaata. Google STT (sun'na) aur
edge-tts (awaaz) internet use karte hain. History `data/history.jsonl` mein save hoti hai
— delete karni ho to file uda do.

**Q: Naya kaam sikhana hai?**
A: `tools.py` mein ek function banao, `TOOLS` aur `TOOL_SCHEMAS` mein naam daal do.
Bas — JARVIS ko naya kaam aa jayega.

---

## 🆘 Abhi bhi atke ho?

CMD mein ye 3 command chalao aur output bhejo:
```
cd jarvis-folder-ka-path
python --version
python check.py
```

Main dekh kar exact solution bata dunga. 💪
