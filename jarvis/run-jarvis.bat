@echo off
chcp 65001 >nul
title JARVIS - Voice Assistant
cd /d %~dp0
echo JARVIS shuru ho raha hai... (Ctrl+C = band)
python jarvis.py %*
if errorlevel 1 (
    echo.
    echo [!] Kuch gadbad. Pehle install.bat chalao.
    pause
)