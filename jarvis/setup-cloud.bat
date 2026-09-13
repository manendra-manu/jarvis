@echo off
chcp 65001 >nul
title Cloud Brain Setup (Groq)
cd /d "%~dp0"
where python >nul 2>&1
if errorlevel 1 (
    echo Python nahi mila! Pehle Python install karo: https://python.org
    pause
    exit /b 1
)
python setup_groq.py
echo.
pause
