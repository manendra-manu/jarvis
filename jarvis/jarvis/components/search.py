"""Web search and info utilities for JARVIS."""
from __future__ import annotations

import re as _re
import urllib.parse
import webbrowser

import requests as _req
from jarvis import config as _config

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def web_search(query: str) -> dict:
    query = (query or "").strip()
    if not query:
        return {"ok": False, "speech": "Kya search karun?", "text": "", "tool": "web_search"}
    try:
        r = _req.get("https://html.duckduckgo.com/html/", params={"q": query}, headers=_HEADERS, timeout=15)
        r.raise_for_status()
        html = r.text
        links = _re.findall(r'result__a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, _re.S)
        out = []
        for href, title in links[:5]:
            title = _re.sub(r"<[^>]+>", "", title).strip()
            m = _re.search(r"uddg=([^&]+)", href)
            url = urllib.parse.unquote(m.group(1)) if m else href
            if title and url.startswith("http"):
                out.append({"title": title, "url": url})
        if not out:
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            return {"ok": True, "speech": f"'{query}' browser mein khol diya.", "text": f"https://www.google.com/search?q={urllib.parse.quote(query)}", "tool": "web_search"}
        top = out[0]
        return {"ok": True, "speech": f"'{query}' ke liye pehla result hai: {top['title']}. Browser mein khol diya.", "text": "\n".join(f"• {o['title']}\n  {o['url']}" for o in out), "tool": "web_search"}
    except Exception as e:
        return {"ok": False, "speech": "Search fail ho gaya, internet check karo.", "text": str(e), "tool": "web_search"}


def wikipedia_summary(topic: str, sentences: int = 3) -> dict:
    topic = (topic or "").strip()
    try:
        if _re.search(r"[ऀ-ॿ]", topic):
            rh = _req.get(f"https://hi.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}", headers=_HEADERS, timeout=15)
            if rh.status_code == 200 and rh.json().get("extract"):
                d = rh.json()
                short = ". ".join(_re.split(r"(?<=[।!?])\s+", d["extract"])[:int(sentences)])
                return {"ok": True, "speech": short, "text": f"{d.get('title')}\n\n{d['extract']}\n\n{d.get('content_urls', {}).get('desktop', {}).get('page', '')}", "tool": "wikipedia_summary"}
        r = _req.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}", headers=_HEADERS, timeout=15)
        if r.status_code != 200:
            r = _req.get("https://en.wikipedia.org/w/api.php", params={"action": "opensearch", "search": topic, "limit": 1, "format": "json"}, headers=_HEADERS, timeout=15)
            names = r.json()[1]
            if not names:
                return {"ok": False, "speech": f"'{topic}' ke baare mein kuch nahi mila.", "text": "", "tool": "wikipedia_summary"}
            topic = names[0]
            r = _req.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(topic)}", headers=_HEADERS, timeout=15)
        data = r.json()
        extract = data.get("extract", "").strip()
        if not extract:
            return {"ok": False, "speech": f"'{topic}' par detail nahi mili.", "text": "", "tool": "wikipedia_summary"}
        short = ". ".join(_re.split(r"(?<=[.!?])\s+", extract)[:int(sentences)])
        return {"ok": True, "speech": short, "text": f"{data.get('title')}\n\n{extract}\n\n{data.get('content_urls', {}).get('desktop', {}).get('page', '')}", "tool": "wikipedia_summary"}
    except Exception as e:
        return {"ok": False, "speech": "Wikipedia se nahi la payi.", "text": str(e), "tool": "wikipedia_summary"}


def get_weather(city: str = "") -> dict:
    city = (city or "").strip() or _config.DEFAULT_CITY
    try:
        r = _req.get(f"https://wttr.in/{urllib.parse.quote(city)}", params={"format": "j1"}, headers=_HEADERS, timeout=15)
        d = r.json()
        cur = d["current_condition"][0]
        temp = cur["temp_C"]
        feels = cur["FeelsLikeC"]
        hum = cur["humidity"]
        desc = cur["weatherDesc"][0]["value"]
        today = d["weather"][0]
        speech = (f"{city} mein abhi {temp} degree hai, {desc.lower()}, humidity {hum} percent. Aaj maximum {today['maxtempC']} aur minimum {today['mintempC']} degree rahega.")
        text = (f"🌤 {city}: {temp}°C (feels {feels}°C), {desc}\n💧 Humidity {hum}%  |  💨 Wind {cur['windspeedKmph']} km/h\n📈 Max {today['maxtempC']}°  📉 Min {today['mintempC']}°")
        return {"ok": True, "speech": speech, "text": text, "tool": "get_weather"}
    except Exception as e:
        return {"ok": False, "speech": f"{city} ka weather nahi la payi.", "text": str(e), "tool": "get_weather"}