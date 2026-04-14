@echo off
:: ─── INDIAN SWING TRADING AI AGENT ───────────────────────────────────────────
:: Runs the swing trading agent automatically
:: Set up in Windows Task Scheduler to run daily at 8 PM
::
:: IMPORTANT: Update the path below to match your actual project location
:: ─────────────────────────────────────────────────────────────────────────────

cd D:\crew_ai_agent\swing-trading-agent
call venv\Scripts\activate
python main.py

:: Keep window open for 10 seconds if there's an error
timeout /t 10
