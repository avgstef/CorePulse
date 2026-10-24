@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ===============================================
echo   CorePulse Windows executable build
 echo ===============================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=py -3"
) else (
    set "PYTHON=python"
)

echo [1/4] Upgrading pip...
%PYTHON% -m pip install --upgrade pip
if errorlevel 1 goto :failure

echo [2/4] Installing CorePulse requirements...
%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 goto :failure

echo [3/4] Installing PyInstaller...
%PYTHON% -m pip install pyinstaller
if errorlevel 1 goto :failure

echo [4/4] Building dist\CorePulse.exe...
%PYTHON% -m PyInstaller --noconfirm --clean --onefile --windowed --name "CorePulse" --icon "assets\corepulse.ico" --add-data "assets;assets" app.py
if errorlevel 1 goto :failure

if not exist "dist\CorePulse.exe" (
    echo Build completed without the expected executable.
    goto :failure
)

echo.
echo ===============================================
echo SUCCESS: dist\CorePulse.exe is ready.
echo ===============================================
echo.
pause
exit /b 0

:failure
echo.
echo ===============================================
echo BUILD FAILED. Review the messages above.
echo ===============================================
echo.
pause
exit /b 1
