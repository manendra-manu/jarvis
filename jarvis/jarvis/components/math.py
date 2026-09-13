"""Safe math evaluation utilities for JARVIS."""
from __future__ import annotations

import ast
import math
import operator
import re

from jarvis import config as _config

_ALLOWED_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
_ALLOWED_FUNCS = {
    "sqrt": math.sqrt, "abs": abs, "round": round, "sin": math.sin,
    "cos": math.cos, "tan": math.tan, "log": math.log, "log10": math.log10,
    "exp": math.exp, "floor": math.floor, "ceil": math.ceil,
    "pow": pow, "min": min, "max": max,
}
_WORD_OPS = [
    ("square root of", "sqrt "), ("square root", "sqrt "), ("vargmul", "sqrt "),
    ("percent of", "/100*"), ("percent", "/100"),
    ("jod", "+"), ("jama", "+"), ("aur", "+"), ("plus", "+"), ("add", "+"),
    ("ghata", "-"), ("minus", "-"), ("subtract", "-"),
    ("guna", "*"), ("gunah", "*"), ("into", "*"), ("times", "*"), ("multiply", "*"),
    ("bhag", "/"), ("divide", "/"), ("divided by", "/"),
]
_EN_NUMS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
            "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15,
            "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100,
            "half": 0.5, "dozen": 12}
_HI_NUMS = {"ek": 1, "do": 2, "teen": 3, "char": 4, "chaar": 4, "panch": 5, "che": 6,
            "chhah": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10, "gyarah": 11,
            "barah": 12, "aadha": 0.5, "savaa": 1.25, "dhai": 2.5, "sava": 1.25}
_FILLER = ["kitna", "kitne", "kitni", "karna", "karo", "kijiye", "hota", "hoti", "hotA",
           "hai", "hain", "tha", "thi", "calculate", "compute", "what", "is", "are",
           "tell", "me", "please", "pls", "batao", "bataye", "batayen", "nikalo",
           "answer", "jawabe", "jawab", "ka", "ki", "ke", "aur", "and", "ya", "the",
           "mujhe", "mera", "karke", "bata", "bolo", "zara", "ji", "haan"]


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.Call):
        name = getattr(node.func, "id", None)
        if name in _ALLOWED_FUNCS and not node.keywords:
            return _ALLOWED_FUNCS[name](*[_eval_node(a) for a in node.args])
    if isinstance(node, ast.Name) and node.id in _ALLOWED_FUNCS:
        return _ALLOWED_FUNCS[node.id]
    raise ValueError("unsupported expression")


def _clean_math(expr: str) -> str:
    e = " " + str(expr or "").lower().strip() + " "
    e = e.translate(str.maketrans("०१२३४५६७८९", "0123456789"))
    for dev, rom in [("प्रतिशत", "percent"), ("गुणा", "guna"), ("जोड़", "plus"),
                       ("जमा", "plus"), ("घटा", "minus"), ("माइनस", "minus"),
                       ("भाग", "divide"), ("वर्गमूल", "square root"), ("का", "ka"),
                       ("की", "ki"), ("के", "ke"), ("कितना", "kitna"), ("होता", "hota"),
                       ("है", "hai")]:
        e = e.replace(dev, f" {rom} ")
    for w, sym in sorted(_WORD_OPS, key=lambda x: -len(x[0])):
        e = re.sub(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", f" {sym} ", e)
    e = e.replace("×", " * ").replace("÷", " / ").replace("^", "**")
    hindi = bool(re.search(r"(?<![a-z0-9])(guna|jama|jod|bhag|kitna|kitne|batao|aadha|dhai|plus|teen|panch|saat|aath|che|nau|das)(?![a-z0-9])", e))
    for w, n in list(_EN_NUMS.items()) + (list(_HI_NUMS.items()) if hindi else []):
        e = re.sub(rf"(?<![a-z0-9]){w}(?![a-z0-9])", f" {n} ", e)
    e = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "*", e)
    e = re.sub(r"\b(sqrt|abs|exp|floor|ceil|log10|log)\s+(\d+(?:\.\d+)?)", r"\1(\2)", e)
    e = re.sub(r"(\d+(?:\.\d+)?)\s+(?:ka|ki|ke)?\s*\b(sqrt|abs|exp|floor|ceil|log10|log)\b", r"\2(\1)", e)
    for w in _FILLER:
        e = re.sub(rf"(?<![a-z0-9]){re.escape(w)}(?![a-z0-9])", " ", e)
    e = re.sub(r"[^0-9a-z\.\+\-\*/\(\)%\s]", " ", e)
    e = re.sub(r"[a-z]+", lambda m: m.group(0) if m.group(0) in _ALLOWED_FUNCS else " ", e)
    e = re.sub(r"\s+", " ", e).strip()
    e = re.sub(r"\b(sqrt|abs|exp|floor|ceil|log10|log)\s+(\d+(?:\.\d+)?)", r"\1(\2)", e)
    e = re.sub(r"(\d)\s+(\d)", r"\1*\2", e)
    e = re.sub(r"(\d)\s+(\()", r"\1*\2", e)
    return e


def do_math(expression: str) -> dict:
    cleaned = _clean_math(expression)
    if not cleaned or not re.search(r"\d", cleaned):
        return {"ok": False, "speech": "Mujhe samajh nahi aaya, hisaab dobara batao.", "text": "", "tool": "do_math"}
    cleaned = re.sub(r"[\+\-\*/]+$", "", cleaned).strip()
    if not cleaned or cleaned[-1] in "*/" or cleaned[0] in "*/":
        return {"ok": False, "speech": "Mujhe samajh nahi aaya, hisaab dobara batao.", "text": cleaned, "tool": "do_math"}
    try:
        tree = ast.parse(cleaned, mode="eval")
        result = _eval_node(tree)
    except Exception:
        return {"ok": False, "speech": "Ye hisaab solve nahi ho paya.", "text": cleaned, "tool": "do_math"}
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    result = round(result, 6) if isinstance(result, float) else result
    return {
        "ok": True,
        "speech": f"Jawab hai {result}",
        "text": f"{cleaned} = {result}",
        "tool": "do_math",
    }