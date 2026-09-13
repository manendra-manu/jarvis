import py_compile
try:
    py_compile.compile(r'D:\jarvis\jarvis\jarvis\tools.py', doraise=True)
    print("OK")
except py_compile.PyCompileError as e:
    print(f"ERROR: {e}")