"""
TC2 — Hardware Technician
==========================
Double-click or run:  python test_cases/run_tc2.py

Starts the server (if not already running), loads 16 Technician candidates
into TalentFlow AI, runs the full Classical AI pipeline, then opens
http://127.0.0.1:8000 in your browser with results ready to explore.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from test_cases._launcher import run_testcase

if __name__ == "__main__":
    run_testcase(2, "TC2 — Hardware Technician  (16 candidates)")
