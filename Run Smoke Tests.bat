@echo off
setlocal
set "APP_DIR=%~dp0"
set "BUNDLED_PY=C:\Users\Tanks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

cd /d "%APP_DIR%"

if exist "%BUNDLED_PY%" (
    "%BUNDLED_PY%" "%APP_DIR%smoke_test.py"
    goto done
)

where py >nul 2>nul
if not errorlevel 1 (
    py "%APP_DIR%smoke_test.py"
    goto done
)

where python >nul 2>nul
if not errorlevel 1 (
    python "%APP_DIR%smoke_test.py"
    goto done
)

echo Python was not found. Install Python 3 with Tkinter, then run this again.

:done
pause
