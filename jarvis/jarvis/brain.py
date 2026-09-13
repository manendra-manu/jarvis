"""
JARVIS ka DIMAAG (brain).
Orchestration: Rule Engine -> Ollama -> Fallback.
"""
from __future__ import annotations

import json
import re
import time
import traceback
from typing import Callable

import requests as _req

from jarvis import config as _config
from jarvis import tools as _tools
from jarvis.rules import rule_engine


def ollama_alive(host: str | None = None) -> bool:
    host = host or _config.OLLAMA_HOST
    try:
        return _req.get(f"{host}/api/tags", timeout=2).status_code == 200
    except Exception:
        return False


def ollama_models(host: str | None = None) -> list:
    host = host or _config.OLLAMA_HOST
    try:
        d = _req.get(f"{host}/api/tags", timeout=3).json()
        return [m["name"] for m in d.get("models", [])]
    except Exception:
        return []


def _call_ollama(messages: list, use_tools: bool = True, host: str | None = None,
                 model: str | None = None, stream: bool = False,
                 on_token: Callable[[str], None] | None = None) -> dict:
    host = host or _config.OLLAMA_HOST
    model = model or _config.OLLAMA_MODEL
    payload = {"model": model, "messages": messages, "stream": stream,
               "options": {"temperature": _config.OLLAMA_TEMPERATURE,
                           "num_predict": _config.OLLAMA_NUM_PREDICT,
                           "num_ctx": _config.OLLAMA_NUM_CTX}}
    if use_tools:
        payload["tools"] = _tools.TOOL_SCHEMAS
    r = _req.post(f"{host}/api/chat", json=payload, timeout=_config.OLLAMA_TIMEOUT, stream=stream)
    r.raise_for_status()
    if not stream:
        return r.json()
    full = ""
    for line in r.iter_lines():
        if not line:
            continue
        try:
            chunk = json.loads(line)
        except Exception:
            continue
        piece = chunk.get("message", {}).get("content", "")
        if piece:
            full += piece
            if on_token:
                on_token(piece)
        if chunk.get("done"):
            break
    return {"message": {"content": full}}


def _call_cloud_msg(messages: list) -> dict:
    """Groq (OpenAI-format) se ek message lao - 1-2 second mein."""
    payload = {"model": _config.GROQ_MODEL, "messages": messages,
               "temperature": _config.OLLAMA_TEMPERATURE,
               "max_tokens": 600, "tools": _tools.TOOL_SCHEMAS}
    r = _req.post(_config.GROQ_URL,
                  headers={"Authorization": f"Bearer {groq_key()}",
                           "Content-Type": "application/json"},
                  json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


class Brain:
    """Main brain that handles conversation and tool-calling."""

    def __init__(self, model: str | None = None, host: str | None = None,
                 system_prompt: str | None = None, keep_history: int = 12,
                 on_thought: Callable[[str], None] | None = None) -> None:
        self.host = host or _config.OLLAMA_HOST
        self.model = model or _config.OLLAMA_MODEL
        self.system_prompt = system_prompt or _config.SYSTEM_PROMPT
        self.keep_history = keep_history
        self.on_thought = on_thought or (lambda s: None)
        self.messages: list[dict] = [{"role": "system", "content": self.system_prompt}]
        self.last_tools: list = []

    def _trim(self) -> None:
        if len(self.messages) > self.keep_history + 1:
            self.messages = [self.messages[0]] + self.messages[-(self.keep_history):]

    def _user_turn(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def _log(self, user_text: str, reply: str) -> None:
        try:
            import datetime as dt
            with open(_config.HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps({"t": dt.datetime.now().isoformat(timespec="seconds"),
                                     "you": user_text, "jarvis": reply}, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def think(self, user_text: str, allow_llm: bool = True) -> dict:
        """Main entry point. Returns {ok, speech, text, tools, source}."""
        user_text = (user_text or "").strip()
        if not user_text:
            return {"ok": False, "speech": "Boliye, main sun rahi hoon.", "text": "", "source": "rule"}
        self.last_tools = []

        rule = rule_engine(user_text)
        if rule:
            self._user_turn(user_text)
            self.messages.append({"role": "assistant", "content": rule.get("speech", "")})
            self.last_tools.append(rule.get("tool", "rule"))
            self._log(user_text, rule.get("speech", ""))
            rule["source"] = "rule"
            return rule

        if allow_llm:
            llm = self._think_llm(user_text)
            if llm is not None:
                return llm

        return self._fallback(user_text)

    def _run_tool_loop(self, get_message) -> dict | None:
        tool_results = []
        for _ in range(4):
            msg = get_message()
            if "role" not in msg:
                msg = {"role": "assistant", **msg}
            calls = msg.get("tool_calls") or []
            if not calls:
                answer = (msg.get("content") or "").strip()
                self.messages.append(msg)
                return self._combine(answer, tool_results)
            self.messages.append(msg)
            for c in calls:
                fn = c.get("function", {})
                name = fn.get("name", "")
                raw = fn.get("arguments", {})
                args = raw if isinstance(raw, dict) else _safe_json(raw)
                self.on_thought(f"Tool chala rahi hoon: {name}")
                res = _tools.run_tool(name, args)
                self.last_tools.append(name)
                tool_results.append(res)
                self.messages.append({
                    "role": "tool",
                    "content": json.dumps({"ok": res.get("ok"), "result": res.get("text") or res.get("speech")},
                                          ensure_ascii=False),
                })
        return self._combine("", tool_results)

    def _think_llm(self, user_text: str) -> dict | None:
        if groq_key():
            try:
                self.on_thought("☁️ Cloud brain (Groq) soch raha hai...")
                self._user_turn(user_text)
                out = self._run_tool_loop(lambda: _call_cloud_msg(self.messages))
                self._log(user_text, out["speech"])
                out["source"] = "llm"
                return out
            except Exception as e:
                self.on_thought(f"Groq error ({type(e).__name__}) - Ollama try...")
                self.messages = self.messages[:-1]
        if not ollama_alive(self.host):
            self.on_thought("Ollama band hai - rule engine use ho raha hai")
            return None
        self.on_thought(f"Ollama ({self.model}) soch raha hai...")
        self._user_turn(user_text)
        try:
            out = self._run_tool_loop(
                lambda: _call_ollama(self.messages, use_tools=True,
                                     host=self.host, model=self.model).get("message", {}))
            self._log(user_text, out["speech"])
            return out
        except _req.exceptions.Timeout:
            self.on_thought("Ollama timeout")
            return None
        except Exception:
            self.on_thought("Ollama error: " + traceback.format_exc(limit=1).strip().splitlines()[-1])
            return None

    def _combine(self, answer: str, tool_results: list) -> dict:
        ok = all(r.get("ok", True) for r in tool_results) if tool_results else True
        text_parts = [r.get("text") for r in tool_results if r.get("text")]
        return {
            "ok": ok,
            "speech": answer or (tool_results[-1].get("speech", "") if tool_results else ""),
            "text": "\n\n".join(text_parts) or answer,
            "tools": [r.get("tool") for r in tool_results if r.get("tool")],
            "source": "llm",
        }

    def _fallback(self, user_text: str) -> dict:
        self._user_turn(user_text)
        s = (f"Sorry, main '{user_text[:40]}' samajh nahi payi. "
             "Aap reminder, time, hisaab, mausam, app kholna, search, ya WhatsApp bol sakte ho.")
        self.messages.append({"role": "assistant", "content": s})
        self._log(user_text, s)
        return {"ok": False, "speech": s, "text": s, "tools": [], "source": "fallback"}

    def think_stream(self, user_text: str, on_token: Callable[[str], None]) -> dict:
        """Streaming response for web UI."""
        user_text = (user_text or "").strip()
        rule = rule_engine(user_text)
        if rule:
            self._user_turn(user_text)
            self.messages.append({"role": "assistant", "content": rule.get("speech", "")})
            for ch in rule.get("speech", ""):
                on_token(ch)
            rule["source"] = "rule"
            self._log(user_text, rule.get("speech", ""))
            return rule
        if not ollama_alive(self.host):
            return self._fallback(user_text)
        self._user_turn(user_text)
        try:
            tool_results = []
            for _ in range(4):
                data = _call_ollama(self.messages, use_tools=True, host=self.host, model=self.model)
                msg = data.get("message", {})
                calls = msg.get("tool_calls") or []
                if not calls:
                    answer = (msg.get("content") or "").strip()
                    self.messages.append({"role": "assistant", "content": answer})
                    for ch in answer:
                        on_token(ch)
                    out = self._combine(answer, tool_results)
                    self._log(user_text, out["speech"])
                    return out
                if "role" not in msg:
                    msg = {"role": "assistant", **msg}
                self.messages.append(msg)
                for c in calls:
                    fn = c.get("function", {})
                    name = fn.get("name", "")
                    raw = fn.get("arguments", {})
                    args = raw if isinstance(raw, dict) else _safe_json(raw)
                    res = _tools.run_tool(name, args)
                    tool_results.append(res)
                    self.last_tools.append(name)
                    self.messages.append({"role": "tool", "content": json.dumps(
                        {"ok": res.get("ok"), "result": res.get("text") or res.get("speech")},
                        ensure_ascii=False)})
            return self._combine("", tool_results)
        except Exception:
            return self._fallback(user_text)

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": self.system_prompt}]


def _safe_json(raw) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        return {}


def groq_key() -> str:
    import os
    return os.environ.get("GROQ_API_KEY", "") or getattr(_config, "GROQ_API_KEY", "") or ""