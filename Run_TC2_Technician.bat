@echo off
title TalentFlow AI -- TC2 Hardware Technician
cd /d "%~dp0"
echo.
echo  Starting TC2 -- Hardware Technician
echo  (16 candidates, any city, 3 openings)
echo.
if not exist ".venv\Scripts\python.exe" (
    echo  ERROR: Virtual environment not found.
    echo  Run:  python -m venv .venv  then  .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
.venv\Scripts\python.exe test_cases\run_tc2.py
if errorlevel 1 (
    echo.
    echo  Something went wrong -- see error above.
    pause
)
