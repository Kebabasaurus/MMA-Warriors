@echo off
setlocal
set "APP_DIR=%~dp0"
set "BUNDLED_PY=C:\Users\Tanks\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "PACKAGE_DIR=%APP_DIR%dist\MMA Warriors"
set "RUNTIME_BACKUP=%APP_DIR%build\package_runtime_backup"

cd /d "%APP_DIR%"

tasklist /FI "IMAGENAME eq MMA Warriors.exe" 2>nul | find /I "MMA Warriors.exe" >nul
if not errorlevel 1 (
    echo MMA Warriors is currently running. Close it before rebuilding the portable folder.
    echo Your current packaged files were not changed.
    pause
    exit /b 1
)

if exist "%BUNDLED_PY%" (
    set "PY=%BUNDLED_PY%"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PY=py"
    ) else (
        where python >nul 2>nul
        if not errorlevel 1 (
            set "PY=python"
        ) else (
            echo Python was not found. Install Python 3 with Tkinter.
            pause
            exit /b 1
        )
    )
)

%PY% "%APP_DIR%smoke_test.py"
if errorlevel 1 (
    echo Smoke tests failed. Fix them before building.
    pause
    exit /b 1
)

%PY% -m pip show pyinstaller >nul 2>nul
if errorlevel 1 (
    echo PyInstaller is not installed for this Python.
    echo Installing PyInstaller now...
    %PY% -m pip install pyinstaller
    if errorlevel 1 (
        echo Could not install PyInstaller.
        pause
        exit /b 1
    )
)

rem PyInstaller replaces dist\MMA Warriors. Preserve runtime data first.
for %%D in (Saves Databases Logs) do (
    if exist "%PACKAGE_DIR%\%%D" (
        if not exist "%RUNTIME_BACKUP%\%%D" mkdir "%RUNTIME_BACKUP%\%%D"
        xcopy /E /I /Y "%PACKAGE_DIR%\%%D" "%RUNTIME_BACKUP%\%%D" >nul
    )
)

%PY% -m PyInstaller --noconfirm --windowed --name "MMA Warriors" --icon "%APP_DIR%assets\app_icon.ico" --add-data "%APP_DIR%assets;assets" --distpath "%APP_DIR%dist" --workpath "%APP_DIR%build" --specpath "%APP_DIR%build" "%APP_DIR%main.py"
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

for %%D in (Saves Databases Logs) do (
    if not exist "%PACKAGE_DIR%\%%D" mkdir "%PACKAGE_DIR%\%%D"
    if exist "%RUNTIME_BACKUP%\%%D" xcopy /E /I /Y "%RUNTIME_BACKUP%\%%D" "%PACKAGE_DIR%\%%D" >nul
)
copy /Y "%APP_DIR%README.md" "%PACKAGE_DIR%\README.md" >nul
copy /Y "%APP_DIR%Portable Check.bat" "%PACKAGE_DIR%\Portable Check.bat" >nul

echo.
echo Build complete:
echo %PACKAGE_DIR%\MMA Warriors.exe
pause
