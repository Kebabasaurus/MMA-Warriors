@echo off
setlocal
set "APP_DIR=%~dp0"
set "LOCAL_PY=%APP_DIR%.venv\Scripts\python.exe"

cd /d "%APP_DIR%"

if exist "%LOCAL_PY%" (
    set "PY=%LOCAL_PY%"
) else (
    where py >nul 2>nul
    if not errorlevel 1 (
        set "PY=py"
    ) else (
        where python >nul 2>nul
        if not errorlevel 1 (
            set "PY=python"
        ) else (
            echo Python 3 with PyInstaller was not found.
            pause
            exit /b 1
        )
    )
)

%PY% "%APP_DIR%database_editor.py" --validate "%APP_DIR%Databases\Default Universe.universe.json"
if errorlevel 1 (
    echo Database validation failed. The editor was not built.
    pause
    exit /b 1
)

%PY% -m PyInstaller --noconfirm --clean --distpath "%APP_DIR%output_database_editor" --workpath "%APP_DIR%build_database_editor" "%APP_DIR%MMA Warriors Database Editor.spec"
if errorlevel 1 (
    echo Build failed.
    pause
    exit /b 1
)

copy /Y "%APP_DIR%output_database_editor\MMA Warriors Database Editor.exe" "%APP_DIR%dist\MMA Warriors\MMA Warriors Database Editor.exe" >nul
echo.
echo Build complete:
echo %APP_DIR%dist\MMA Warriors\MMA Warriors Database Editor.exe
pause
