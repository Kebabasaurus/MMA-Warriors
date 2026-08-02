@echo off
setlocal
set "APP_DIR=%~dp0"
set "LOCAL_PY=%APP_DIR%.venv\Scripts\python.exe"

cd /d "%APP_DIR%"

if exist "%LOCAL_PY%" set "PY=%LOCAL_PY%"

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

%PY% "%APP_DIR%persistence_regression_test.py"
if errorlevel 1 goto failed

%PY% "%APP_DIR%contracts_finance_regression_test.py"
if errorlevel 1 goto failed

%PY% "%APP_DIR%ui_data_regression_test.py"
if errorlevel 1 goto failed

%PY% "%APP_DIR%qa_tooling_regression_test.py"
if errorlevel 1 goto failed

%PY% "%APP_DIR%stability_test.py"
if errorlevel 1 goto failed

%PY% "%APP_DIR%media_system_test.py"
if errorlevel 1 goto failed

echo.
echo Shipping and focused Brett-Dev regression playtests passed.
goto done

:failed
echo.
echo A shipping test failed. Review the traceback above before building.

:done
pause
