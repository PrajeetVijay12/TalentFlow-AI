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

# ── resolve paths ─────────────────────────────────────────────────────────────
ROOT     = Path(__file__).resolve().parent.parent          # project root
VENV_PY  = ROOT / ".venv" / "Scripts" / "python.exe"      # Windows venv

TC_EMAIL    = "tc_demo@talentflow.ai"
TC_PASSWORD = "TcDemo@99"
TC_NAME     = "TC Demo User"
BASE_URL    = "http://127.0.0.1:8000"

# ── colours ───────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"
CYAN   = "\033[96m"; BOLD   = "\033[1m";  RESET = "\033[0m"

def _c(t, col): return f"{col}{t}{RESET}"
def info(msg):    print(f"  {_c('►', CYAN)} {msg}")
def ok(msg):      print(f"  {_c('✓', GREEN)} {msg}")
def warn(msg):    print(f"  {_c('!', YELLOW)} {msg}")
def err(msg):     print(f"  {_c('✗', RED)} {msg}"); sys.exit(1)


def _python() -> str:
    """Return the venv Python if it exists, else the current interpreter."""
    return str(VENV_PY) if VENV_PY.exists() else sys.executable


def _server_running() -> bool:
    try:
        import httpx
        return httpx.get(f"{BASE_URL}/api/health", timeout=2).status_code == 200
    except Exception:
        return False


def _start_server() -> subprocess.Popen:
    info("Starting TalentFlow AI server …")
    proc = subprocess.Popen(
        [_python(), "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # poll until healthy (up to 20 s)
    for _ in range(40):
        time.sleep(0.5)
        if _server_running():
            ok("Server is up at http://127.0.0.1:8000")
            return proc
    err("Server did not start within 20 s — check that port 8000 is free.")


def _auth(client) -> None:
    """Register (or login if already registered)."""
    import httpx
    r = client.post(f"{BASE_URL}/api/auth/register",
                    json={"name": TC_NAME, "email": TC_EMAIL, "password": TC_PASSWORD})
    if r.status_code == 200:
        ok(f"Registered as {TC_EMAIL}")
        return
    if r.status_code == 409:        # user already exists — log in
        r2 = client.post(f"{BASE_URL}/api/auth/login",
                         json={"email": TC_EMAIL, "password": TC_PASSWORD})
        if r2.status_code == 200:
            ok(f"Logged in as {TC_EMAIL}")
            return
        err(f"Login failed: {r2.text}")
    err(f"Auth failed ({r.status_code}): {r.text}")


def run_testcase(n: int, label: str) -> None:
    import httpx

    print(f"\n{BOLD}{CYAN}{'='*62}{RESET}")
    print(f"{BOLD}{CYAN}  TalentFlow AI — {label}{RESET}")
    print(f"{BOLD}{CYAN}{'='*62}{RESET}\n")

    # ── 1. Ensure server is running ───────────────────────────────────────────
    server_proc = None
    if _server_running():
        ok("Server already running at http://127.0.0.1:8000")
    else:
        server_proc = _start_server()

    # ── 2. Authenticate ───────────────────────────────────────────────────────
    info("Authenticating …")
    with httpx.Client(base_url=BASE_URL) as client:
        _auth(client)

        # ── 3. Load test case ─────────────────────────────────────────────────
        info(f"Loading test case {n} into the app …")
        r = client.post(f"/api/testcase/{n}", timeout=180)
        if r.status_code != 200:
            err(f"Failed to load TC{n}: {r.text}")
        data = r.json()

        ok(f"Test case loaded!  {data['total']} candidates processed.")
        print(f"\n  {BOLD}Results{RESET}")
        print(f"    {_c('Selected : ' + str(data['selected']),  GREEN)}")
        print(f"    {_c('Wait List: ' + str(data['waitlist']), YELLOW)}")
        print(f"    {_c('Rejected : ' + str(data['rejected']),  RED)}")

    # ── 4. Open browser ───────────────────────────────────────────────────────
    print()
    info("Opening browser …")
    webbrowser.open(f"{BASE_URL}/shortlist")
    ok("Done!  Navigate to any page — all TC data is loaded.\n")

    # ── 5. Keep server alive ──────────────────────────────────────────────────
    if server_proc:
        print(f"  {BOLD}Server running. Press Ctrl+C to stop.{RESET}\n")
        try:
            server_proc.wait()
        except KeyboardInterrupt:
            server_proc.terminate()
            print("\n  Server stopped.")
    else:
        print(f"  {BOLD}(Server was already running — not stopped by this script){RESET}\n")
