@echo off
setlocal
set "APP_DIR=%~dp0"
set "PY=C:\Users\Tanks\AppData\Local\Programs\Python\Python313\python.exe"

cd /d "%APP_DIR%"

if not exist "%PY%" (
    echo Python 3.13 with PyInstaller was not found.
    pause
    exit /b 1
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
