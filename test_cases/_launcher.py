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

TC_EMAIL    = "tc_demo@talentflow.ai"
TC_PASSWORD = "TcDemo@99"
TC_NAME     = "TC Demo User"
BASE_URL    = "http://127.0.0.1:8000"

# ── print helpers (flush=True so output appears immediately in .bat windows) ──
def _p(sym, msg, end="\n"):
    print(f"  {sym} {msg}", end=end, flush=True)

def info(msg):  _p(">>", msg)
def ok(msg):    _p("OK", msg)
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


def _post_json(url: str, body: dict, cookies: dict) -> tuple[int, dict, dict]:
    """Minimal JSON POST using only stdlib. Returns (status, json_body, new_cookies)."""
    import json, urllib.request, urllib.error, http.cookiejar

    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"})
    # attach existing cookies
    if cookies:
        req.add_header("Cookie", "; ".join(f"{k}={v}" for k, v in cookies.items()))

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            resp_body = json.loads(resp.read())
            # parse Set-Cookie header(s)
            new_cookies = dict(cookies)
            for line in resp.headers.get_all("Set-Cookie") or []:
                part = line.split(";")[0].strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    new_cookies[k.strip()] = v.strip()
            return resp.status, resp_body, new_cookies
    except urllib.error.HTTPError as e:
        resp_body = {}
        try:
            resp_body = json.loads(e.read())
        except Exception:
            pass
        return e.code, resp_body, cookies


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
        # Poll until healthy (up to 30 s)
        for i in range(60):
            time.sleep(0.5)
            if _server_running():
                ok(f"Server is up  (took {(i+1)*0.5:.1f}s)")
                break
            if i == 59:
                fail("Server did not start in 30 s — is port 8000 free?")

    # ── 2. Authenticate ───────────────────────────────────────────────────────
    info("Authenticating ...")
    cookies: dict = {}

    status, _, cookies = _post_json(
        f"{BASE_URL}/api/auth/register",
        {"name": TC_NAME, "email": TC_EMAIL, "password": TC_PASSWORD},
        cookies,
    )
    if status == 200:
        ok(f"Registered as {TC_EMAIL}")
    elif status == 409:
        status2, _, cookies = _post_json(
            f"{BASE_URL}/api/auth/login",
            {"email": TC_EMAIL, "password": TC_PASSWORD},
            cookies,
        )
        if status2 == 200:
            ok(f"Logged in as {TC_EMAIL}")
        else:
            fail(f"Login failed (HTTP {status2})")
    else:
        fail(f"Auth failed (HTTP {status})")

    # ── 3. Load test case ─────────────────────────────────────────────────────
    info(f"Loading test case {n} and running pipeline (may take ~30 s) ...")
    status3, data, _ = _post_json(
        f"{BASE_URL}/api/testcase/{n}", {}, cookies,
    )
    if status3 != 200:
        fail(f"Failed to load TC{n}: {data}")

    ok(f"Test case loaded!  {data['total']} candidates processed.")
    print(flush=True)
    print(f"    Selected : {data['selected']}", flush=True)
    print(f"    Wait List: {data['waitlist']}", flush=True)
    print(f"    Rejected : {data['rejected']}", flush=True)

    # ── 4. Open browser ───────────────────────────────────────────────────────
    print(flush=True)
    info("Opening browser ...")
    time.sleep(1)
    webbrowser.open(f"{BASE_URL}/shortlist")
    ok(f"Done!  Browser opened to http://127.0.0.1:8000/shortlist")

    # ── 5. Keep server alive ──────────────────────────────────────────────────
    print(flush=True)
    if server_proc:
        print("  Server is running. Close this window (or press Ctrl+C) to stop it.\n", flush=True)
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
