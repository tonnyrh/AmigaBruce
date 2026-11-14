@echo off
python "%~dp0tools\build_audio_test_page.py" --open
if errorlevel 1 (
    echo Unable to open the audio test page. Check that Python is installed.
    pause
    exit /b 1
)
