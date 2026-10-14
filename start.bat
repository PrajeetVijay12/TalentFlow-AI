@echo off
REM One-click launcher for Windows. Double-click this file.
cd /d "%~dp0"

if not exist .venv (
  echo Creating Python environment...
  python -m venv .venv
  .venv\Scripts\python -m pip install -r requirements.txt
)
if not exist frontend\node_modules (
  echo Installing frontend packages...
  cd frontend && call npm install && cd ..
)
if not exist frontend\dist\index.html (
  echo Building the web app...
  cd frontend && call npm run build && cd ..
)

echo.
echo Starting... open http://127.0.0.1:8000 in your browser (Ctrl+C to stop)
start "" http://127.0.0.1:8000
.venv\Scripts\python -m uvicorn backend.main:app --port 8000
