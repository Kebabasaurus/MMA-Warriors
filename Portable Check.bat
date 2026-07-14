@echo off
setlocal
set "APP_DIR=%~dp0"

echo MMA Warriors Portable Check
echo.

if not exist "%APP_DIR%MMA Warriors.exe" (
    echo ERROR: MMA Warriors.exe was not found beside this check.
    echo Extract or copy the entire MMA Warriors folder before running it.
    pause
    exit /b 1
)

for %%D in (Saves Databases Logs) do (
    if not exist "%APP_DIR%%%D" mkdir "%APP_DIR%%%D" 2>nul
)

set "PROBE=%APP_DIR%.mma_warriors_portable_check.tmp"
> "%PROBE%" echo MMA Warriors portable folder write check
if not exist "%PROBE%" (
    echo WARNING: This folder is protected. The game will use:
    echo %LOCALAPPDATA%\MMA Warriors
    echo.
) else (
    del "%PROBE%" >nul 2>nul
    echo This folder is writable. Saves and logs will stay beside the EXE.
    echo.
)

echo The portable build is ready to launch.
pause
