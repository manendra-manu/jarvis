from __future__ import annotations

import datetime as dt
import platform
import shutil
import subprocess
import time as _time
import urllib.parse
import webbrowser
from pathlib import Path

from jarvis import config as _config

IS_WINDOWS = platform.system() == "Windows"

DEV_APPS = {
    "नोटपैड": "notepad", "नोट पैड": "notepad", "कैलकुलेटर": "calculator",
    "केलकुलेटर": "calculator", "गणक": "calculator", "क्रोम": "chrome",
    "पेंट": "paint", "वर्ड": "word", "एक्सेल": "excel", "एक्सप्लोरर": "explorer",
    "फाइल एक्सप्लोरर": "explorer", "कैमरा": "camera", "सेटिंग्स": "settings",
    "सेटिंग": "settings", "स्पॉटिफाई": "spotify", "व्हाट्सएप": "whatsapp",
    "ब्राउज़र": "browser", "पावरशेल": "powershell", "टास्क मैनेजर": "task manager",
}


def get_time() -> dict:
    now = dt.datetime.now()
    s = now.strftime("%I:%M %p").lstrip("0")
    d = now.strftime("%A, %d %B %Y")
    return {"ok": True, "speech": f"Abhi {s}, {d}.", "text": f"{s} | {d}", "tool": "get_time"}


def get_date() -> dict:
    d = dt.datetime.now().strftime("%A, %d %B %Y")
    return {"ok": True, "speech": f"Aaj {d}.", "text": d, "tool": "get_date"}


def open_app(app: str) -> dict:
    key = (app or "").strip().lower()
    key = DEV_APPS.get(key, key)
    if not key:
        return {"ok": False, "speech": "Kaunsi app kholun?", "text": "", "tool": "open_app"}
    cmd = _config.APP_COMMANDS.get(key)
    if not cmd:
        for k, v in _config.APP_COMMANDS.items():
            if k in key or key in k:
                cmd = v
                break
    if cmd:
        try:
            args = cmd.split() if isinstance(cmd, str) else cmd
            subprocess.Popen(args, creationflags=(0x08000000 if IS_WINDOWS else 0))
            return {"ok": True, "speech": f"{key} khol rahi hoon.", "text": f"▶ {cmd}", "tool": "open_app"}
        except Exception as e:
            return {"ok": False, "speech": f"{key} nikhul paya.", "text": str(e), "tool": "open_app"}
    if "." in key:
        url = key if key.startswith("http") else f"https://{key}"
        webbrowser.open(url)
        return {"ok": True, "speech": f"{key} khol rahi hoon.", "text": url, "tool": "open_app"}
    exe = shutil.which(key) or shutil.which(key.replace(" ", ""))
    if exe:
        subprocess.Popen([exe])
        return {"ok": True, "speech": f"{key} khol rahi hoon.", "text": exe, "tool": "open_app"}
    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(key + ' app')}")
    return {"ok": False, "speech": f"{key} nahi mila, browser mein dhoondh rahi hoon.", "text": key, "tool": "open_app"}


def open_website(url: str) -> dict:
    url = (url or "").strip()
    if not url:
        return {"ok": False, "speech": "Kaunsi website?", "text": "", "tool": "open_website"}
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return {"ok": True, "speech": f"{url.split('//')[1].split('/')[0]} khol rahi hoon.", "text": url, "tool": "open_website"}


def _yt_first_video(q: str) -> str | None:
    import re as _re
    try:
        r = _requests_get("https://www.youtube.com/results", params={"search_query": q}, timeout=15)
        m = _re.search(r'"videoId":"([\w-]{11})"', r.text)
        return m.group(1) if m else None
    except Exception:
        return None


def _requests_get(url, **kwargs):
    import requests as _req
    return _req.get(url, timeout=kwargs.pop("timeout", 15), **kwargs)


def play_media(query: str = "", kind: str = "youtube") -> dict:
    q = (query or "").strip()
    kind = (kind or "youtube").lower()
    if kind.startswith("spo") or "spotify" in kind:
        url = (f"https://open.spotify.com/search/{urllib.parse.quote(q)}"
               if q else "https://open.spotify.com")
        speech = f"Spotify pe '{q}' chala rahi hoon." if q else "Spotify khol rahi hoon."
    elif q:
        vid = _yt_first_video(q)
        if vid:
            url = f"https://www.youtube.com/watch?v={vid}"
            speech = f"YouTube pe '{q}' chala diya hai - suniye!"
        else:
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(q + ' song')}"
            speech = f"YouTube pe '{q}' chala rahi hoon."
    else:
        url = "https://www.youtube.com"
        speech = "YouTube khol rahi hoon - trending mein kuch accha laga lena."
    webbrowser.open(url)
    return {"ok": True, "speech": speech, "text": url, "tool": "play_media"}


def volume(action: str = "up") -> dict:
    import ctypes
    action = (action or "up").lower()
    if not IS_WINDOWS:
        return {"ok": False, "speech": "Ye sirf Windows pe chalta hai.", "text": platform.system(), "tool": "volume"}
    try:
        VK = {"up": 0xAF, "down": 0xAE, "mute": 0xAD}[action]
        for _ in range(5 if action != "mute" else 1):
            ctypes.windll.user32.keybd_event(VK, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK, 0, 2, 0)
            _time.sleep(0.05)
        return {"ok": True, "speech": f"Volume {action}.", "text": f"🔊 {action}", "tool": "volume"}
    except Exception as e:
        return {"ok": False, "speech": "Volume control nahi kar payi.", "text": str(e), "tool": "volume"}


def search_file(name: str, folder: str = "") -> dict:
    name = (name or "").strip().lower()
    if not name:
        return {"ok": False, "speech": "Kaunsi file dhoondhun?", "text": "", "tool": "search_file"}
    if folder:
        roots = [folder]
    else:
        roots = [r for r in _config.SEARCH_FOLDERS if Path(r).exists()]
        if not roots:
            roots = [str(Path.home())]
    found = []
    for root in roots:
        p = Path(root)
        if not p.exists():
            continue
        for f in p.rglob("*"):
            if name in f.name.lower():
                found.append(str(f))
                if len(found) >= 8:
                    break
        if len(found) >= 8:
            break
    if not found:
        return {"ok": False, "speech": f"'{name}' naam ki file nahi mili.", "text": "\n".join(roots), "tool": "search_file"}
    return {
        "ok": True,
        "speech": f"{len(found)} file mili. Pehli: {Path(found[0]).name}",
        "text": "\n".join(f"• {x}" for x in found),
        "tool": "search_file",
    }


def system_info() -> dict:
    try:
        import psutil
        bat = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        lines = [f"💻 {platform.system()} {platform.release()} on {platform.node()}",
                 f"🧠 CPU {cpu}%  |  🗂 RAM {mem.percent}% ({mem.used // (1024**3)} GB / {mem.total // (1024**3)} GB)"]
        speech = f"CPU {int(cpu)} percent, RAM {int(mem.percent)} percent use ho rahi hai."
        if bat:
            lines.append(f"🔋 Battery {int(bat.percent)}% ({'charging' if bat.power_plugged else 'on battery'})")
            speech += f", battery {int(bat.percent)} percent."
        return {"ok": True, "speech": speech, "text": "\n".join(lines), "tool": "system_info"}
    except Exception as e:
        return {"ok": True, "speech": f"Ye {platform.system()} machine hai.", "text": str(e), "tool": "system_info"}


def system_control(action: str) -> dict:
    action = (action or "").lower()
    if not IS_WINDOWS:
        return {"ok": False, "speech": "Ye sirf Windows pe chalta hai.", "text": platform.system(), "tool": "system_control"}
    cmds = {"shutdown": "shutdown /s /t 30", "restart": "shutdown /r /t 30",
            "lock": "rundll32.exe user32.dll,LockWorkStation", "sleep": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"}
    cmd = cmds.get(action)
    if not cmd:
        return {"ok": False, "speech": "Ye action nahi pata.", "text": action, "tool": "system_control"}
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    subprocess.run(cmd.split(), check=False, creationflags=0x08000000 if IS_WINDOWS else 0,
                   startupinfo=si, timeout=5)
    speech = ("PC 30 second mein band ho jayega. Rokne ke liye 'cancel shutdown' bolo."
              if action == "shutdown" else "PC 30 second mein restart hoga." if action == "restart"
              else "PC lock kar diya." if action == "lock" else "PC sleep kar rahi hoon.")
    return {"ok": True, "speech": speech, "text": cmd, "tool": "system_control"}


def cancel_shutdown() -> dict:
    if not IS_WINDOWS:
        return {"ok": False, "speech": "Ye sirf Windows pe.", "text": "", "tool": "cancel_shutdown"}
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    subprocess.run(["shutdown", "/a"], check=False, creationflags=0x08000000 if IS_WINDOWS else 0,
                   startupinfo=si, timeout=5)
    return {"ok": True, "speech": "Shutdown cancel kar diya.", "text": "shutdown /a", "tool": "cancel_shutdown"}


def screenshot(path: str = "") -> dict:
    path = path or str(_config.DATA_DIR / f"shot_{int(_time.time())}.png")
    try:
        import pyautogui
        pyautogui.screenshot(path)
        return {"ok": True, "speech": "Screenshot le liya.", "text": path, "tool": "screenshot"}
    except Exception as e:
        return {"ok": False, "speech": "Screenshot nahi le payi. pyautogui install karo.", "text": str(e), "tool": "screenshot"}


def send_whatsapp(number: str = "", message: str = "") -> dict:
    import re as _re
    message = (message or "").strip()
    number = _re.sub(r"[^\d+]", "", number or "")
    if number.startswith("0"):
        number = "+91" + number.lstrip("0")
    elif number and not number.startswith("+"):
        number = "+91" + number
    if not number:
        return {"ok": False, "speech": "Kis number pe bhejun?", "text": "", "tool": "send_whatsapp"}
    if not message:
        return {"ok": False, "speech": "Kya message likhun?", "text": "", "tool": "send_whatsapp"}
    try:
        import pywhatkit as kit
        now = dt.datetime.now() + dt.timedelta(minutes=1)
        kit.sendwhatmsg(number, message, now.hour, now.minute, wait_time=15, tab_close=True)
        return {"ok": True, "speech": f"Message {number} pe bhej diya.", "text": f"{number}: {message}", "tool": "send_whatsapp"}
    except ImportError:
        url = f"https://wa.me/{number.replace('+', '')}?text={urllib.parse.quote(message)}"
        webbrowser.open(url)
        return {"ok": True, "speech": "WhatsApp browser mein khol diya. Bas send daba do.", "text": url, "tool": "send_whatsapp"}
    except Exception as e:
        return {"ok": False, "speech": "Message nahi bhej payi.", "text": str(e), "tool": "send_whatsapp"}


def send_email(to: str = "", subject: str = "", body: str = "") -> dict:
    to = (to or "").strip()
    if not to:
        return {"ok": False, "speech": "Kisko email karun?", "text": "", "tool": "send_email"}
    url = f"mailto:{urllib.parse.quote(to)}?subject={urllib.parse.quote(subject or '')}&body={urllib.parse.quote(body or '')}"
    webbrowser.open(url)
    return {"ok": True, "speech": f"{to} ke liye email khol diya.", "text": url, "tool": "send_email"}


def joke() -> dict:
    import random
    jokes = [
        "Teacher: Tum late kyun aaye? Student: Aap ne hi kaha tha, jitna jaldi aana ho utna aaram se aana!",
        "Programmer ki girlfriend: Doodh le aao, agar ande mile to ek dozen le aana. Wo 12 doodh le aaya!",
        "WiFi ka password kya hai? Padosi: 'galti se mista ke' type karo.",
        "Doctor: Aapko aaram ki zaroorat hai. Patient: Toh phir mujhe neend kyun nahi aati? Doctor: Kyunki aap sochte rehte ho!",
    ]
    j = random.choice(jokes)
    return {"ok": True, "speech": j, "text": j, "tool": "joke"}


def compliment() -> dict:
    import random
    lines = ["Aap kamaal karte ho!", "Aapke bina to main adhoori hoon!",
             "Boss, aap to legend ho!", "Aapka kaam bolta hai!"]
    l = random.choice(lines)
    return {"ok": True, "speech": l, "text": l, "tool": "compliment"}


# Tool registry — master TOOLS and TOOL_SCHEMAS live in jarvis/tools.py
TOOLS = {}