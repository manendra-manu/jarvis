@echo off
chcp 65001 >nul
title JARVIS - .EXE bana rahe hain
cd /d %~dp0
echo.
echo  PyInstaller se JARVIS.exe bana rahe hain (3-6 min)...
echo.
python -m pip install pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [X] PyInstaller install nahi hua. Manual install karo: pip install pyinstaller
    pause
    exit /b 1
)
pyinstaller --noconfirm --onefile --console --name JARVIS ^
  --add-data "web;web" ^
  --hidden-import=jarvis ^
  --hidden-import=jarvis.config ^
  --hidden-import=jarvis.components ^
  --hidden-import=jarvis.tools ^
  jarvis.py
echo.
echo  Ho gaya!  dist\JARVIS.exe  ->  double click karke chalao.
echo  (web UI ke liye 'web' folder exe ke paas rakhna)
pause