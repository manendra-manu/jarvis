"""Test script to verify all imports work after refactoring."""
import sys
sys.path.insert(0, '.')

print("Testing imports...")

try:
    import config
    print(f"  [OK] config: {config.ASSISTANT_NAME}")
except Exception as e:
    print(f"  [FAIL] config: {e}")

try:
    import tools
    print(f"  [OK] tools: {len(tools.TOOLS)} tools")
except Exception as e:
    print(f"  [FAIL] tools: {e}")

try:
    import brain
    print("  [OK] brain imported")
except Exception as e:
    print(f"  [FAIL] brain: {e}")

try:
    import rules
    print("  [OK] rules imported")
except Exception as e:
    print(f"  [FAIL] rules: {e}")

try:
    from components.math import do_math
    print("  [OK] components.math")
except Exception as e:
    print(f"  [FAIL] components.math: {e}")

try:
    from components.reminders import scheduler, set_reminder
    print("  [OK] components.reminders")
except Exception as e:
    print(f"  [FAIL] components.reminders: {e}")

try:
    from components.system import open_app, get_weather
    print("  [OK] components.system")
except Exception as e:
    print(f"  [FAIL] components.system: {e}")

try:
    import speak
    print("  [OK] speak imported")
except Exception as e:
    print(f"  [FAIL] speak: {e}")

try:
    import listen
    print("  [OK] listen imported")
except Exception as e:
    print(f"  [FAIL] listen: {e}")

try:
    import webapp
    print("  [OK] webapp imported")
except Exception as e:
    print(f"  [FAIL] webapp: {e}")

try:
    import brain
    r = brain.rule_engine("kitne baje hain")
    if r and r.get("ok"):
        print(f"  [OK] rule_engine test: {r['speech'][:30]}")
    else:
        print("  [FAIL] rule_engine returned None or not ok")
except Exception as e:
    print(f"  [FAIL] rule_engine test: {e}")

try:
    r = tools.do_math("250 * 4 + 15")
    if r.get("ok") and "1015" in r.get("text", ""):
        print(f"  [OK] do_math test: {r['text']}")
    else:
        print(f"  [FAIL] do_math: {r}")
except Exception as e:
    print(f"  [FAIL] do_math: {e}")

try:
    s = speak.Speaker(muted=True)
    s.say("test")
    print("  [OK] Speaker muted works")
except Exception as e:
    print(f"  [FAIL] Speaker: {e}")

try:
    from tests.test_jarvis import TestTools
    print("  [OK] tests importable")
except Exception as e:
    print(f"  [FAIL] tests import: {e}")

print("\nDone!")