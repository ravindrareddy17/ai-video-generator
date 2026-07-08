@echo off
echo ==================================================
echo   Starting AI Video Generator V2 Automated Run
echo ==================================================

:: Navigate to the project directory
cd /d "E:\ai_gen\AI-VIDEO-V2"

:: Log with timestamp
echo Running at %date% %time% >> logs\automation.log

:: Execute the pipeline with the pinned project interpreter first
py -3.12 python/main.py >> logs\automation.log 2>&1
if %ERRORLEVEL% neq 0 (
    echo [WARN] Python 3.12 launch failed. Falling back to default python on PATH. >> logs\automation.log
    python python/main.py >> logs\automation.log 2>&1
)

:: Check the exit code
if %ERRORLEVEL% equ 0 (
    echo [SUCCESS] Pipeline completed successfully. >> logs\automation.log
) else (
    echo [ERROR] Pipeline failed with exit code %ERRORLEVEL%. >> logs\automation.log
)
