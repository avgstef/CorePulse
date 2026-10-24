@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 app.py
) else (
    python app.py
)

if errorlevel 1 (
    echo.
    echo CorePulse exited with an error. Ensure dependencies are installed with:
    echo     py -3 -m pip install -r requirements.txt
    pause
)
endlocal
