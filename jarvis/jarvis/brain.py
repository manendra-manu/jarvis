"""
JARVIS ka DIMAAG (brain) - Groq Primary + Fallback.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import traceback
from pathlib import Path
from typing import Callable

import requests as _req
from dotenv import load_dotenv

from jarvis import config as _config
from jarvis import tools as _tools
from jarvis.rules import rule_engine

# Load .env file automatically
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()


def groq_key() -> str:
    """Get Groq API Key from environment or config."""
    return os.environ.get("GROQ_API_KEY", "") or getattr(_config, "GROQ_API_KEY", "") or ""


def _call_cloud_msg(messages: list) -> dict:
    """Groq Cloud LLM Call (1-2 Second Response)."""
    key = groq_key()
    if not key:
        raise ValueError("GROQ_API_KEY missing!")

    model = os.environ.get("GROQ_MODEL") or getattr(_config, "GROQ_MODEL", "llama-3.3-70b-versatile")
    url = getattr(_config, "GROQ_URL", "https://api.groq.com/openai/v1/chat/completions")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 600,
        "tools": _tools.TOOL_SCHEMAS
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    r = _req.post(url, headers=headers, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]


def _safe_json(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {}


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
            self.messages = [self.messages[0]] + self.messages[-self.keep_history:]

    def _user_turn(self, text: str) -> None:
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def think(self, user_text: str) -> dict:
        """Main entry point. Returns {ok, speech, text, tools, source}."""
        user_text = (user_text or "").strip()
        if not user_text:
            return {"ok": False, "speech": "Boliye, main sun rahi hoon.", "text": "", "source": "rule"}

        self.last_tools = []

        # 1. Check Rule Engine
        rule = rule_engine(user_text)
        if rule:
            self._user_turn(user_text)
            self.messages.append({"role": "assistant", "content": rule.get("speech", "")})
            rule["source"] = "rule"
            return rule

        # 2. Try Groq AI Cloud Brain
        self._user_turn(user_text)
        if groq_key():
            try:
                self.on_thought("☁️ Groq AI soch raha hai...")
                tool_results = []
                for _ in range(3):
                    msg = _call_cloud_msg(self.messages)
                    if "role" not in msg:
                        msg = {"role": "assistant", **msg}

                    calls = msg.get("tool_calls") or []
                    if not calls:
                        answer = (msg.get("content") or "").strip()
                        self.messages.append(msg)
                        return {
                            "ok": True,
                            "speech": answer,
                            "text": answer,
                            "tools": [r.get("tool") for r in tool_results if r.get("tool")],
                            "source": "llm"
                        }

                    self.messages.append(msg)
                    for c in calls:
                        fn = c.get("function", {})
                        name = fn.get("name", "")
                        args = _safe_json(fn.get("arguments", {}))
                        self.on_thought(f"Tool: {name}")
                        res = _tools.run_tool(name, args)
                        tool_results.append(res)
                        self.messages.append({
                            "role": "tool",
                            "content": json.dumps({"ok": res.get("ok"), "result": res.get("text") or res.get("speech")}, ensure_ascii=False)
                        })

                answer = self.messages[-1].get("content", "")
                return {"ok": True, "speech": answer, "text": answer, "tools": [], "source": "llm"}
            except Exception as e:
                self.on_thought(f"Groq Error: {e}")
                self.messages = self.messages[:-1]

        # 3. Fallback Response
        s = "Mujhe samajh nahi aaya. Aap mausam, time, hisaab, ya general sawal pooch sakte ho."
        self.messages.append({"role": "assistant", "content": s})
        return {"ok": False, "speech": s, "text": s, "tools": [], "source": "fallback"}

    def reset(self) -> None:
        self.messages = [{"role": "system", "content": self.system_prompt}]