@echo off
setlocal
set "APP_DIR=%~dp0"
set "BUNDLED_PY=C:\Users\Tanks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

cd /d "%APP_DIR%"

if exist "%BUNDLED_PY%" set "PY=%BUNDLED_PY%"

if not defined PY (
    where py >nul 2>nul
    if not errorlevel 1 set "PY=py"
)

if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)

if not defined PY (
    echo Python was not found. Install Python 3 with Tkinter, then run this again.
    goto done
)

%PY% "%APP_DIR%smoke_test.py"
if errorlevel 1 goto failed

%PY% "%APP_DIR%stability_test.py"
if errorlevel 1 goto failed

%PY% "%APP_DIR%media_system_test.py"
if errorlevel 1 goto failed

echo.
echo Smoke, stability, and media-system playtests passed.
goto done

:failed
echo.
echo A shipping test failed. Review the traceback above before building.

:done
pause
