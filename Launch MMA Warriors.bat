@echo off
setlocal
set "APP_DIR=%~dp0"
set "LOCAL_PY=%APP_DIR%.venv\Scripts\python.exe"

cd /d "%APP_DIR%"

rem Prefer the packaged build if it has been created.
if exist "%APP_DIR%dist\MMA Warriors\MMA Warriors.exe" (
    start "MMA Warriors" "%APP_DIR%dist\MMA Warriors\MMA Warriors.exe"
    exit /b
)

rem Otherwise run from source with the best available Python.
if exist "%LOCAL_PY%" (
    start "MMA Warriors" "%LOCAL_PY%" "%APP_DIR%main.py"
    exit /b
)

where py >nul 2>nul
if not errorlevel 1 (
    start "MMA Warriors" py "%APP_DIR%main.py"
    exit /b
)

where python >nul 2>nul
if not errorlevel 1 (
    start "MMA Warriors" python "%APP_DIR%main.py"
    exit /b
)

echo Python was not found. Install Python 3 (with Tkinter) or build the game first.
pause
