# 📘 JARVIS — Pura User Manual (bilkul aasan bhasha mein)

> Yaad rakhiye: **Terminal mein mic button nahi hota, kyunki zaroorat hi nahi —
> JARVIS ka mic hamesha SUNTA rehta hai. Aapki awaaz hi button hai.** 🎤

JARVIS use karne ke **2 tarike** hain:

| Tarika | File | Kaise bolte hain |
|---|---|---|
| 🖥️ **Terminal (asli JARVIS feel)** | `run-jarvis.bat` | Bina button ke, seedha bol kar |
| 🌐 **Browser (button wala)** | `run-web.bat` | Mic **button** daba kar (http://localhost:8000) |

---

# 🖥️ PART 1 — Terminal wala JARVIS (step-by-step)

## 🎀 Awaaz (voice) badalni ho to

1. **`change-voice.bat`** double-click karo
2. Numbered list aayegi (Hindi + English female voices)
3. Number likho (jaise `3`) → Enter → awaaz save!
4. `run-jarvis.bat` chalao — nayi awaaz mein bolegi

Pasand na aaye to dobara change-voice.bat. Manual tareeka: `config.py` mein
`EDGE_VOICE = "hi-IN-SwaraNeural"` line badlo. Kuch famous female awaazein:
`hi-IN-SwaraNeural` (Hindi), `en-IN-NeerjaNeural` (Indian English),
`en-US-JennyNeural` / `en-US-AriaNeural` (US English).
Ek baar ke liye try karna ho: `python jarvis.py --voice en-US-JennyNeural`

## ☁️ Cloud Fast Brain (Groq) - smart jawab 1-2 second mein

Local Ollama CPU pe dheema hai (10-60 sec). Free cloud brain se sab 1-2 sec:

1. **`setup-cloud.bat`** double-click karo
2. Browser khulega (console.groq.com/keys) → **Google se sign-in** → **Create API Key** → copy (gsk_ se shuru)
3. Black window mein **right-click → paste → Enter**
4. "KEY KAAM KAR RAHI HAI!" dikhe → `run-jarvis.bat` chalao

Banner mein dikhega: `☁️ Cloud brain: ON (Groq ...)`. Bina card, bilkul free.
Net nahi hai to apne aap local Ollama pe laut jaati hai.

## 1) Shuru karna
`D:\jarvis\jarvis` mein **`run-jarvis.bat`** pe double click karo.

Screen pe ye aayega:
```
🧠 Ollama: ONLINE   models: llama3.1:8b
🔊 Awaaz: edge, gTTS, say
🎤 Mic backend: sounddevice
🎤 Sun rahi hoon... bolo: jarvis, hey jarvis, hi jarvis   ← isi ka matlab: mic ON hai
```
Aur JARVIS **bol kar** kahegi: *"Namaste! Main JARVIS hoon…"*

## 2) Baat karne ka cycle (ye samajh lo, bas!)

```
   JARVIS chup-chaap sunti rehti hai        (screen: "Sun rahi hoon...")
              │
   Aap bolo:  "hey jarvis"                  ← ye hi MIC BUTTON hai 🎤
              │
   JARVIS:    "Ji boss?"                    ← ab turant apna kaam bolo
              │
   Aap bolo:  "kitne baje hain"
              │
   JARVIS:    boli "Abhi raat 9 baje hain"  + screen pe bhi likha
              │
   (wapas sunti reh gayi — cycle repeat)
```

**Bas ye hi poora manual hai!** 😄 Koi button dabana nahi hota.

## 3) 4 sunehri baatein (bolne ke rules)

1. **"Ji boss?" sunte hi 8 second ke andar bolo** — warna wo kahegi *"Maine kuch suna nahi"* → phir dobara *"hey jarvis"* bolo.
2. **JARVIS jab bol rahi ho, tab mat bolo** — pehle uski baat khatam hone do, phir *"hey jarvis"*.
3. **Laptop ke mic ke thoda paas (haath bhar door) saaf bolo.**
4. Hinglish mein bolo — *"reminder laga"*, *"gaana chalao"* — English accent ki zaroorat nahi.
5. **Hindi (Devanagari) mein bhi bol sakte ho** — *"कितने बजे हैं"*, *"गाना बजाओ"* — sab turant samjha jaata hai.

## 4) Agar wake word ki jhanjhat nahi chahiye
CMD mein ye chalao:
```
D:\jarvis\jarvis\run-jarvis.bat --nowake
```
Ab **"hey jarvis" bolne ki zaroorat nahi** — wo har baar sunti hai, seedha kaam bolo:
*"kitne baje hain"* → turant jawab.

## 5) Mic se nahi, type karke baat karni ho
```
python jarvis.py --text
```
Likho → Enter → jawab. (Mic kharab ho to ye zindagi bachata hai.)

## 6) Band karna
Window pe **X** daba do, ya **Ctrl + C**. JARVIS so jayegi. 😴

## 7) Screen ke neeche wali chhoti line ka matlab
```
[rule-engine | tool: - | 0.0s]    ← bijli-fast: fixed commands (gaana, time, reminder)
[ollama:llama3.1:8b | 6.2s]       ← dimaag wala jawab (6 second laga, normal hai)
```

---

# 🌐 PART 2 — Browser wala JARVIS (button wala)

1. **`run-web.bat`** pe double click → browser khulega: **http://localhost:8000**
2. Beech mein ek **gol chamakta orb** hai — **wo hi MIC BUTTON hai**. Us pe click karo.
3. Pehli baar browser poochhega *"Microphone use karne du?"* → **Allow** karo.
4. Orb **hara** ho jayega = sun rahi hai → **bolo** → rukte hi khud bhej degi → jawab likhegi + **bolegi**.
5. Neeche box mein **type** karke bhi baat kar sakte ho → ➤ dabao.

**Orb ke rang:**
| Rang | Matlab |
|---|---|
| 🔵 neela chamak | ready / khali baithi hai |
| 🟢 hara | **sun rahi hai — boliye!** |
| 🟡 peela | soch rahi hai |
| 🔵 dhadakta | **bol rahi hai** |

**Button guide:**
| Button | Kaam |
|---|---|
| 🎤 (bada gol) | mic on/off |
| ➤ | likha hua bhejo |
| 🔊 | JARVIS ki awaaz on/off |
| ↻ | chat saaf karo |

> 📱 Phone se: PC aur phone same WiFi pe → phone mein `http://192.168.1.X:8000`
> (PC pe `ipconfig` chalao, IPv4 Address wala number daalo).

---

# 🗣️ PART 3 — Kya-kya bol sakte ho (poori list)

Pehle **"hey jarvis"** (ya `--nowake` mein seedha):

### ⏰ Time / Date
- *"kitne baje hain"*
- *"aaj ki date kya hai"* / *"aaj kaun sa din hai"*

### ⏰ Reminder
- *"10 minute baad paani peene ka reminder laga"*
- *"shaam 6 baje meeting ka reminder"*
- *"kal subah 9 baje gym ka reminder laga"*
- *"kaunse reminder hain"* / *"saare reminder delete karo"*

### 🧮 Hisaab
- *"250 guna 4 plus 15 kitna hota hai"*
- *"100 ka 15 percent"*
- *"144 ka square root"*

### 📝 Notes
- *"note karo doodh lana hai"*
- *"mere notes dikha"*

### 🌤️ Mausam / Jankari
- *"jabalpur ka mausam"* / *"bhopal ka weather"*
- *"virat kohli kaun hai"*
- *"taj mahal ke baare mein bata"*
- *"python search karo"*

### 💻 Computer
- *"notepad kholo"* / *"calculator chalao"*
- *"google.com kholo"*
- *"resume file dhoondho"*
- *"volume up"* / *"volume down"* / *"mute"*
- *"system info"* (battery, RAM)
- *"screenshot lo"*
- *"shutdown karo"* → (30 sec milte hain) → *"cancel shutdown"*

### 🎵 Music
- *"arijit singh ka gaana chalao"*
- *"youtube se gana bajao"*
- *"gana sunao"*
- *"spotify pe tum hi ho chalao"*

### 💬 Message
- *"whatsapp bhej 9876543210 main aa raha hoon"*
- *"email bhej ravi@gmail.com kal meeting hai"*

### 🧠 Smart baatein (Ollama se — 3–8 sec lagta hai)
- *"mera mood off hai, motivate karo"*
- *"mujhe Excel sikhni hai, 7 din ka plan banao"*
- *"bachon ko English kaise sikhayen"*
- *"ek joke sunao"* 😄
- *"tum kaun ho"* / *"thank you"* / *"bye"*

---

# 🆘 PART 4 — Problems & ilaaj

| Problem | Ilaj |
|---|---|
| JARVIS ne suna hi nahi | Thoda paas jaake, saaf bolo. Mic permission ON hai? (Settings → Privacy → Microphone) |
| *"Maine kuch suna nahi"* aaya | Normal hai — dobara *"hey jarvis"* bolo |
| Galat samjha (Google ne galat likha) | Thoda dheere bolo; Hinglish chalti hai |
| Jawab mein 10–30 sec lag rahe | Wo Ollama (dimaag) wala jawab hai. Tez chahiye: `--model llama3.2:3b` |
| Gaana/app 0 second mein khulna chahiye | Wo rule-engine wale commands hain — upar wali list jaisa bolo |
| JARVIS bol nahi rahi | 🔊 Check: `pip install edge-tts` ; ya web UI mein 🔊 button on karo |
| Terminal band kiya to reminder nahi baja | Reminder sirf **chalu** JARVIS bajata hai (band karne se pehle wale restart pe chalenge) |
| Browser wala mic nahi chalta | Chrome/Edge use karo; address bar mein mic icon → Allow |

---

# 📅 Roz ka routine

| Subah PC on kiya | Kya karo |
|---|---|
| 1 | 🦙 Ollama khud chalu hai (tray mein icon) |
| 2 | `run-jarvis.bat` double click (ya Desktop shortcut) |
| 3 | *"hey jarvis"* → din shuru! ☀️ |
| Raat ko | Window band (X) — bye JARVIS 👋 |

**Bas! Itna hi hai poora manual. Ab boliye — "hey jarvis…"** 🤖💙
