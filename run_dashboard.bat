@echo off
setlocal

cd /d "%~dp0"

py -3.12 python\dashboard_app.py
if %ERRORLEVEL% equ 0 (
    exit /b 0
)

echo [WARN] Python 3.12 launch failed. Falling back to the default python on PATH.
python python\dashboard_app.py
