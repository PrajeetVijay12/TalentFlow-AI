"""
Shared launcher logic used by run_tc1.py / run_tc2.py / run_tc3.py.
Not meant to be run directly.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"
BASE_URL = "http://127.0.0.1:8000"


def _p(sym, msg):
    print(f"  {sym} {msg}", flush=True)

def info(msg): _p(">>", msg)
def ok(msg):   _p("OK", msg)

def fail(msg):
    _p("!!", msg)
    try:
        input("\n  Press Enter to close.")
    except (EOFError, OSError):
        pass
    sys.exit(1)


def _python() -> str:
    return str(VENV_PY) if VENV_PY.exists() else sys.executable


def _server_running() -> bool:
    try:
        import urllib.request
        with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def run_testcase(n: int, label: str) -> None:
    print(f"\n{'='*62}", flush=True)
    print(f"  TalentFlow AI  --  {label}", flush=True)
    print(f"{'='*62}\n", flush=True)

    # ── 1. Ensure server is running ───────────────────────────────────────────
    server_proc = None
    if _server_running():
        ok("Server already running at http://127.0.0.1:8000")
    else:
        info("Starting TalentFlow AI server ...")
        server_proc = subprocess.Popen(
            [_python(), "-m", "uvicorn", "backend.main:app",
             "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(ROOT),
        )
        for i in range(60):
            time.sleep(0.5)
            if _server_running():
                ok(f"Server is up  (took {(i+1)*0.5:.1f}s)")
                break
            if i == 59:
                fail("Server did not start in 30 s — is port 8000 free?")

    # ── 2. Open the launch URL — the server logs in + loads data + redirects ─
    launch_url = f"{BASE_URL}/api/testcase/launch/{n}"
    info(f"Opening browser — loading test case {n} ...")
    info(f"URL: {launch_url}")
    time.sleep(1)
    webbrowser.open(launch_url)
    ok("Browser opened!  The pipeline will start automatically —")
    ok("watch each stage run, then results appear when done.\n")

    # ── 3. Keep server alive ──────────────────────────────────────────────────
    if server_proc:
        print("  Server is running. Close this window (or Ctrl+C) to stop.\n", flush=True)
        try:
            server_proc.wait()
        except KeyboardInterrupt:
            server_proc.terminate()
            print("\n  Server stopped.", flush=True)
    else:
        print("  (Server was already running — this script will not stop it.)\n", flush=True)
        try:
            input("  Press Enter to close.")
        except (EOFError, OSError):
            pass
