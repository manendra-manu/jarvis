@echo off
chcp 65001 >nul
title JARVIS - Web UI
cd /d %~dp0
echo.
echo  JARVIS web khul raha hai...
echo  Browser:  http://localhost:8000
echo  Phone  :  http://^<PC ka IP^>:8000     (ipconfig se IP dekho)
echo  Band karne ke liye: Ctrl+C
echo.
start "" http://localhost:8000
python jarvis.py --web