@echo off
chcp 65001 >nul
title JARVIS - Health Check
cd /d %~dp0
echo.
echo  ==========================================================
echo     J A R V I S   -   KYA READY HAI?   (Health Check)
echo  ==========================================================
echo.
python check.py
echo.
pause