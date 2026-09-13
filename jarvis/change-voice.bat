@echo off
chcp 65001 >nul
title JARVIS Awaaz Badlo
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
    echo Python nahi mila!
    pause
    exit /b 1
)
python change_voice.py
echo.
pause
