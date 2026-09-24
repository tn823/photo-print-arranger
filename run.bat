@echo off
chcp 65001 > nul
title Photo Print Arranger
cd /d "%~dp0"

echo Dang khoi dong Photo Print Arranger...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LOI] Khong the chay ung dung. Vui long kiem tra da cai Python va cac thu vien:
    echo pip install -r requirements.txt
    pause
)
