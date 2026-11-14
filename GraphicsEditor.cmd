@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0edit-amiga-graphics.ps1"
if errorlevel 1 (
    echo Press any key to close this window.
    pause >nul
    exit /b 1
)
