@echo off
chcp 65001 >nul

REM FIX encoding (P3): Set UTF-8 so symbols display correctly in logs

echo ============================================================
echo   Indian Swing Trading AI Agent
echo   Starting run: %DATE% %TIME%
echo ============================================================

REM FIX P2: Use /d flag to switch drive AND directory in one command
cd /d D:\crew_ai_agent\swing-trading-agent
if %ERRORLEVEL% neq 0 (
    echo ERROR: Could not change to project directory.
    echo Check that D:\crew_ai_agent\swing-trading-agent exists.
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate
if %ERRORLEVEL% neq 0 (
    echo ERROR: Could not activate virtual environment.
    echo Check that venv\ exists inside the project folder.
    exit /b 1
)

REM Run the agent
python swing_main.py

REM FIX P1: Capture Python exit code IMMEDIATELY before anything else runs
set PYTHON_EXIT=%ERRORLEVEL%

REM Log result to console
if %PYTHON_EXIT% equ 0 (
    echo.
    echo SUCCESS: Agent completed at %TIME%
) else (
    echo.
    echo FAILED: Agent exited with code %PYTHON_EXIT% at %TIME%
    echo Check swing_agent.log for error details.
)

REM Brief pause only for manual runs (readable in console)
timeout /t 5 >nul

REM FIX P1: Exit with Python actual exit code so Task Scheduler reports failures correctly
exit /b %PYTHON_EXIT%
