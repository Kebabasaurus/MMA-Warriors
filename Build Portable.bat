@echo off
setlocal
set "APP_DIR=%~dp0"
set "LOCAL_PY=%APP_DIR%.venv\Scripts\python.exe"
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
            echo Python was not found. Install Python 3 with Tkinter.
            pause
            exit /b 1
        )
    )
)

"%PY%" "%APP_DIR%tools\verify_build_toolchain.py" --root "%CD%"
if errorlevel 1 (
    echo Build toolchain verification failed. No packages were installed.
    pause
    exit /b 1
)

"%PY%" "%APP_DIR%run_regression_suite.py"
if errorlevel 1 (
    echo Isolated regression suite failed. Fix it before building.
    pause
    exit /b 1
)

rem PyInstaller replaces dist\MMA Warriors. Preserve runtime data first.
if exist "%RUNTIME_BACKUP%" rmdir /S /Q "%RUNTIME_BACKUP%"
if exist "%RUNTIME_BACKUP%" (
    echo Could not clear the previous runtime-data backup. The portable package was not changed.
    pause
    exit /b 1
)
mkdir "%RUNTIME_BACKUP%"
if errorlevel 1 (
    echo Could not create the runtime-data backup folder. The portable package was not changed.
    pause
    exit /b 1
)
for %%D in (Saves Databases Logs) do (
    if exist "%PACKAGE_DIR%\%%D" (
        mkdir "%RUNTIME_BACKUP%\%%D"
        if errorlevel 1 goto backup_failed
        xcopy /E /I /H /K /Y "%PACKAGE_DIR%\%%D\*" "%RUNTIME_BACKUP%\%%D\" >nul
        if errorlevel 2 goto backup_failed
    )
)
set "RUNTIME_BACKUP_READY=1"

"%PY%" -m PyInstaller --noconfirm --windowed --name "MMA Warriors" --icon "%APP_DIR%assets\app_icon.ico" --add-data "%APP_DIR%assets;assets" --add-data "%APP_DIR%country_flags;country_flags" --distpath "%APP_DIR%dist" --workpath "%APP_DIR%build" --specpath "%APP_DIR%build" "%APP_DIR%main.py"
if errorlevel 1 (
    echo Build failed.
    goto build_failed
)

"%PY%" "%APP_DIR%database_editor.py" --validate "%APP_DIR%Databases\Default Universe.universe.json"
if errorlevel 1 (
    echo Database validation failed. The portable package was not completed.
    goto build_failed
)

"%PY%" -m PyInstaller --noconfirm --clean --distpath "%APP_DIR%output_database_editor" --workpath "%APP_DIR%build_database_editor" "%APP_DIR%MMA Warriors Database Editor.spec"
if errorlevel 1 (
    echo Database Editor build failed. The portable package was not completed.
    goto build_failed
)

if not exist "%PACKAGE_DIR%\MMA Warriors.exe" (
    echo The game build did not produce MMA Warriors.exe.
    goto build_failed
)
if not exist "%APP_DIR%output_database_editor\MMA Warriors Database Editor.exe" (
    echo The Database Editor build did not produce its executable.
    goto build_failed
)

for %%D in (Saves Databases Logs) do (
    if not exist "%PACKAGE_DIR%\%%D" (
        mkdir "%PACKAGE_DIR%\%%D"
        if errorlevel 1 goto build_failed
    )
    if exist "%RUNTIME_BACKUP%\%%D" (
        xcopy /E /I /H /K /Y "%RUNTIME_BACKUP%\%%D\*" "%PACKAGE_DIR%\%%D\" >nul
        if errorlevel 2 goto build_failed
    )
)
copy /Y "%APP_DIR%README.md" "%PACKAGE_DIR%\README.md" >nul
if errorlevel 1 goto build_failed
copy /Y "%APP_DIR%Portable Check.bat" "%PACKAGE_DIR%\Portable Check.bat" >nul
if errorlevel 1 goto build_failed
copy /Y "%APP_DIR%output_database_editor\MMA Warriors Database Editor.exe" "%PACKAGE_DIR%\MMA Warriors Database Editor.exe" >nul
if errorlevel 1 goto build_failed
if not exist "%PACKAGE_DIR%\MMA Warriors Database Editor.exe" goto build_failed

rmdir /S /Q "%RUNTIME_BACKUP%"
if exist "%RUNTIME_BACKUP%" (
    echo Build output is complete, but the temporary runtime-data backup could not be removed.
    echo Remove this folder before the next build: %RUNTIME_BACKUP%
    pause
    exit /b 1
)

echo.
echo Build complete:
echo %PACKAGE_DIR%\MMA Warriors.exe
echo %PACKAGE_DIR%\MMA Warriors Database Editor.exe
pause
exit /b 0

:backup_failed
echo Could not preserve the packaged runtime data. The portable package was not changed.
if exist "%RUNTIME_BACKUP%" rmdir /S /Q "%RUNTIME_BACKUP%"
if exist "%RUNTIME_BACKUP%" echo WARNING: Could not remove the incomplete backup at %RUNTIME_BACKUP%
pause
exit /b 1

:build_failed
if defined RUNTIME_BACKUP_READY (
    call :restore_runtime_after_failure
    if errorlevel 1 (
        echo WARNING: The build failed and the packaged runtime data could not be fully restored.
        echo The preserved copy remains at: %RUNTIME_BACKUP%
    ) else (
        rmdir /S /Q "%RUNTIME_BACKUP%"
        if exist "%RUNTIME_BACKUP%" echo WARNING: Could not remove the temporary backup at %RUNTIME_BACKUP%
    )
)
pause
exit /b 1

:restore_runtime_after_failure
if not exist "%PACKAGE_DIR%" (
    mkdir "%PACKAGE_DIR%"
    if errorlevel 1 exit /b 1
)
for %%D in (Saves Databases Logs) do (
    if exist "%PACKAGE_DIR%\%%D" rmdir /S /Q "%PACKAGE_DIR%\%%D"
    if exist "%PACKAGE_DIR%\%%D" exit /b 1
    if exist "%RUNTIME_BACKUP%\%%D" (
        mkdir "%PACKAGE_DIR%\%%D"
        if errorlevel 1 exit /b 1
        xcopy /E /I /H /K /Y "%RUNTIME_BACKUP%\%%D\*" "%PACKAGE_DIR%\%%D\" >nul
        if errorlevel 2 exit /b 1
    )
)
exit /b 0
