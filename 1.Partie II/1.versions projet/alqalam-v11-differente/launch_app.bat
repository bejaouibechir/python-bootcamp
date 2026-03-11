@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (
    py -3 main.py
) else (
    python main.py
)

if %errorlevel% neq 0 (
    echo.
    echo Echec du lancement. Verifiez Python et les dependances.
    pause
)
endlocal
