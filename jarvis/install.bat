@echo off
chcp 65001 >nul
title JARVIS - Setup
cd /d %~dp0
echo.
echo  ==========================================================
echo     J A R V I S   -   SETUP   (sirf ek baar chalana hai)
echo  ==========================================================
echo.

REM ---------- 1) Python hai ya nahi ----------
where python >nul 2>nul
if errorlevel 1 (
    echo  [X] Python nahi mila!
    echo.
    echo      1. Ye link kholo:  https://www.python.org/downloads/
    echo      2. "Download Python 3.x.x" dabaao
    echo      3. Install karte waqt sabse neeche
    echo         "Add python.exe to PATH"  ^<-- YE TICK KARNA ZAROORI HAI
    echo      4. Install ke baad ye file dobara chalao
    echo.
    pause
    exit /b 1
)

echo  [1/5] Python mil gaya:
python --version
echo.

REM ---------- 2) Python 3.10+ ----------
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if errorlevel 1 (
    echo  [X] Aapka Python purana hai!  JARVIS ke liye Python 3.10 ya naya chahiye.
    echo      Naya Python:  https://www.python.org/downloads/
    echo      ^("Add python.exe to PATH" tick karna mat bhoolna^)
    echo.
    pause
    exit /b 1
)
echo  [2/5] Python version theek hai (3.10+)
echo.

REM ---------- 3) core packages ----------
echo  [3/5] Zaroori packages install ho rahe hain... (2-4 min, internet chahiye)
echo.
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo  [!] Kuch packages atke. Ek-ek karke try kar rahe hain...
    for %%p in (requests fastapi pydantic httpx edge-tts gTTS SpeechRecognition "playsound==1.2.2" pygame psutil sounddevice numpy) do (
        python -m pip install %%p >nul 2>nul || echo       fail: %%p
    )
)
echo.

REM ---------- 4) optional packages ----------
echo  [4/5] Optional packages...
echo        ^[ye fail ho jaayein tab bhi JARVIS chalega - tension mat lo^]
python -m pip install -r requirements-optional.txt >nul 2>&1
echo.

REM ---------- 5) test ----------
echo  [5/5] Test chal rahe hain...
echo.
python -m unittest discover -s tests
echo.

echo  ==========================================================
echo     SETUP POORA!  Ab ye chalao:
echo.
echo        run-jarvis.bat    -  voice assistant (mic se baat)
echo        run-web.bat       -  browser wala JARVIS
echo        check.bat         -  kya-kya ready hai, ye batata hai
echo.
echo     SMART jawab chahiye to Ollama install karo (free):
echo        1. https://ollama.com/download  se install
echo        2. CMD mein:  ollama pull llama3.1:8b
echo.
echo     Poora guide:  SETUP-GUIDE.md  file kholo
echo  ==========================================================
echo.
pause