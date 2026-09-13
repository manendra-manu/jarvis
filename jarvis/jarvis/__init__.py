"""
JARVIS - Personal Voice Assistant (Hinglish).
"""
from __future__ import annotations

__version__ = "2.0.0"
__author__ = "JARVIS"

# Shortcut imports so you can do `from jarvis import Brain, Speaker, Listener`
try:
    from jarvis.brain import Brain
    from jarvis.listen import Listener
    from jarvis.speak import Speaker, say

    __all__ = ["Brain", "Speaker", "Listener", "say", "__version__", "__author__"]
except ImportError:
    # Circular import ya setup ke waqt safe rahe
    pass