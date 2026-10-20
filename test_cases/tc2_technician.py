"""
TC2 — Hardware Technician
==========================
16 candidates with varied hardware/networking profiles.
Run from the project root:  python test_cases/tc2_technician.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.models.schemas import CandidateProfile, JobRequirements, Project
from backend.services.pipeline import run_pipeline

# ─── Job Definition ──────────────────────────────────────────────────────────
JOB = JobRequirements(
    title="Hardware Technician",
    required_degrees=["Diploma", "B.Tech", "B.E."],
    degrees_equivalent=True,
    min_cgpa=6.0,
    min_experience=0.5,
    required_skills=["Hardware Repair", "Networking", "Troubleshooting"],
    required_certifications=["CCNA"],
    certifications_mandatory=False,
    skills_mandatory=True,
    location=None,           # any city
    openings=3,
    weights={"skills": 0.35, "experience": 0.35, "projects": 0.15, "certifications": 0.15},
    thresholds={"selected": 75, "waitlist": 55},
)

# ─── Candidates ──────────────────────────────────────────────────────────────
def P(id_, name, degree, cgpa, exp, skills, certs, location, projects=None):
    return CandidateProfile(
        id=id_, filename=f"{name.replace(' ','_').lower()}.pdf",
        name=name, degree=degree, cgpa=cgpa, experience=exp,
        skills=skills, certifications=certs, location=location,
        projects=projects or [Project(name="Lab Work", category="mini")],
    )

CANDIDATES = [
    # ── Strong / Should be SELECTED ──────────────────────────────────────────
    P(1,  "Ramesh Naidu",       "Diploma", 7.8, 3.0,
        ["Hardware Repair","Networking","Troubleshooting","Circuit Testing","Soldering"],
        ["CCNA"], "Chennai",
        [Project(name="LAN Setup for School Lab",   category="college_major"),
         Project(name="Server Rack Installation",    category="mini")]),

    P(2,  "Lakshmi Varma",      "B.Tech",  7.2, 2.0,
        ["Hardware Repair","Networking","Troubleshooting","Linux","Oscilloscope"],
        ["CCNA"], "Hyderabad",
        [Project(name="Network Monitoring Tool",     category="college_major"),
         Project(name="PCB Fault Detection System",  category="major")]),

    P(3,  "Dinesh Kumar",       "Diploma", 7.0, 4.0,
        ["Hardware Repair","Networking","Troubleshooting","PLC Programming","CCTV Setup"],
        ["CCNA","Security+"], "Coimbatore",
        [Project(name="Factory Floor Network",       category="major"),
         Project(name="CCTV Integration",            category="mini")]),

    P(4,  "Meera Pillai",       "B.E.",    7.5, 2.5,
        ["Hardware Repair","Networking","Troubleshooting","Wireless Config","VoIP"],
        ["CCNA"], "Kochi",
        [Project(name="Office Wi-Fi Rollout",        category="college_major"),
         Project(name="VoIP PBX Setup",              category="mini")]),

    P(5,  "Sunil Patil",        "Diploma", 6.8, 1.5,
        ["Hardware Repair","Networking","Troubleshooting","Soldering","UPS Maintenance"],
        ["CCNA"], "Pune",
        [Project(name="Server UPS Upgrade",          category="mini")]),

    # ── Borderline / Should be WAIT LIST ─────────────────────────────────────
    P(6,  "Geetha Rajan",       "Diploma", 6.5, 0.5,
        ["Hardware Repair","Networking","Troubleshooting"],
        [],      "Chennai",                              # no cert (not mandatory)
        [Project(name="Classroom Projector Setup",   category="mini")]),

    P(7,  "Anil Sharma",        "B.Tech",  6.2, 1.0,
        ["Hardware Repair","Troubleshooting","Soldering","Circuit Testing"],   # missing Networking
        ["CCNA"], "Delhi",
        [Project(name="Embedded Sensor Module",      category="mini")]),

    P(8,  "Farhan Sheikh",      "Diploma", 6.1, 0.5,
        ["Hardware Repair","Networking","Troubleshooting"],
        ["CCNA"], "Mumbai",
        [Project(name="Cable Tray Installation",     category="mini")]),

    # ── Ineligible — wrong degree ─────────────────────────────────────────────
    P(9,  "Tanya Mehta",        "B.Sc",    7.0, 2.0,
        ["Hardware Repair","Networking","Troubleshooting"],
        ["CCNA"], "Bengaluru"),

    P(10, "Vijay Nair",         "B.Com",   6.5, 1.0,
        ["Hardware Repair","Networking","Troubleshooting"],
        ["CCNA"], "Chennai"),

    # ── Ineligible — low CGPA ────────────────────────────────────────────────
    P(11, "Kavitha Sundaram",   "Diploma", 5.2, 1.5,
        ["Hardware Repair","Networking","Troubleshooting"],
        ["CCNA"], "Coimbatore",
        [Project(name="Computer Lab Wiring",         category="mini")]),

    P(12, "Raju Krishnan",      "B.Tech",  5.8, 2.0,
        ["Hardware Repair","Networking","Troubleshooting"],
        ["CCNA"], "Hyderabad"),

    # ── Ineligible — insufficient experience ─────────────────────────────────
    P(13, "Preethi Rao",        "Diploma", 7.5, 0.0,  # fresher
        ["Hardware Repair","Networking","Troubleshooting"],
        ["CCNA"], "Chennai",
        [Project(name="Final Year Lab Setup",        category="college_major")]),

    # ── Ineligible — missing required skills ─────────────────────────────────
    P(14, "Mohan Babu",         "Diploma", 6.8, 1.5,
        ["Circuit Testing","Soldering","UPS Maintenance"],  # no core skills
        ["CCNA"], "Chennai"),

    P(15, "Swetha Iyer",        "B.Tech",  7.1, 1.0,
        ["Linux","Python","Networking"],                    # missing Hardware Repair + Troubleshooting
        [], "Bengaluru",
        [Project(name="Network Traffic Analyser",    category="mini")]),

    P(16, "Harish Balan",       "B.E.",    6.9, 2.5,
        ["Hardware Repair","CCTV Setup","UPS Maintenance"], # missing Networking + Troubleshooting
        ["CCNA"], "Madurai"),
]

# ─── Runner + Display ────────────────────────────────────────────────────────
GREEN  = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"; CYAN = "\033[96m"
BOLD   = "\033[1m";  RESET  = "\033[0m"
STATUS_CLR = {"Selected": GREEN, "Wait List": YELLOW, "Rejected": RED}

def clr(text, color): return f"{color}{text}{RESET}"

def run():
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  TC2 — Hardware Technician  •  16 Candidates{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

    print(f"{BOLD}Job Requirements{RESET}")
    print(f"  Role     : {JOB.title}")
    print(f"  Degrees  : {', '.join(JOB.required_degrees)}")
    print(f"  Min CGPA : {JOB.min_cgpa}  |  Min Exp : {JOB.min_experience} yr")
    print(f"  Skills   : {', '.join(JOB.required_skills)}")
    print(f"  Certs    : {', '.join(JOB.required_certifications)} (not mandatory)")
    print(f"  Location : Any  |  Openings : {JOB.openings}\n")

    result = run_pipeline(JOB, CANDIDATES)

    s = result["summary"]
    print(f"{BOLD}Pipeline Summary{RESET}")
    print(f"  Total: {s['total']}  |  Eligible: {s['eligible']}  |  CSP-valid: {s['csp_valid']}")
    print(f"  {clr('Selected: ' + str(s['Selected']), GREEN)}  "
          f"{clr('Wait List: ' + str(s['Wait List']), YELLOW)}  "
          f"{clr('Rejected: ' + str(s['Rejected']), RED)}\n")

    hdr = f"{'Rank':<5} {'Candidate':<22} {'Status':<10} {'Score':>6} {'Elig':>5} {'CSP':>5} {'FC':>4} {'BC':>4}  Reason"
    print(f"{BOLD}{hdr}{RESET}")
    print("─" * 95)

    by_id = {c["id"]: c for c in result["candidates"]}
    for row in result["ranking"]:
        c      = by_id[row["id"]]
        st     = row["status"]
        sc     = f"{row['score']:.0f}" if row["score"] is not None else "—"
        el     = "✓" if c["eligibility"]["eligible"] else "✗"
        csp    = "✓" if c["csp"]["valid"] else "✗"
        fc     = "✓" if c["forward_chaining"]["goal_reached"] else "✗"
        bc     = "✓" if c["backward_chaining"]["proven"] else "✗"
        reason = c["final"]["reasons"][0] if c["final"]["reasons"] else ""
        reason = reason[:48] + "…" if len(reason) > 48 else reason
        color  = STATUS_CLR.get(st, RESET)
        print(f"{row['rank']:<5} {row['name']:<22} {clr(st, color):<19} {sc:>6} "
              f"  {el:>2}    {csp:>2}   {fc:>2}   {bc:>2}  {reason}")

    print(f"\n{BOLD}Algorithm Stages{RESET}")
    for st in result["stages"]:
        print(f"  [{st['algorithm']:40s}]  {st['ms']:6.1f} ms  — {st['summary'][:70]}")

    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}\n")

if __name__ == "__main__":
    run()
