"""
TC1 — Software Development Engineer (SDE)
==========================================
18 candidates with varied profiles.
Run from the project root:  python test_cases/tc1_sde.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.models.schemas import CandidateProfile, JobRequirements, Project
from backend.services.pipeline import run_pipeline

# ─── Job Definition ──────────────────────────────────────────────────────────
JOB = JobRequirements(
    title="Software Development Engineer",
    required_degrees=["B.Tech", "M.Tech", "B.E.", "M.E."],
    min_cgpa=7.5,
    min_experience=1.0,
    required_skills=["Python", "Java", "SQL", "Data Structures"],
    required_certifications=["AWS"],
    certifications_mandatory=False,
    skills_mandatory=True,
    location="Bengaluru",
    openings=3,
)

# ─── Candidates ───────────────────────────────────────────────────────────────
def P(id_, name, degree, cgpa, exp, skills, certs, location, projects=None):
    return CandidateProfile(
        id=id_, filename=f"{name.replace(' ','_').lower()}.pdf",
        name=name, degree=degree, cgpa=cgpa, experience=exp,
        skills=skills, certifications=certs, location=location,
        projects=projects or [Project(name="Academic Project", category="mini")],
    )

CANDIDATES = [
    # ── Strong / Should be SELECTED ───────────────────────────────────────────
    P(1,  "Aakash Sharma",      "B.Tech", 8.9, 3.0,
        ["Python","Java","SQL","Data Structures","Docker","React"],
        ["AWS"], "Bengaluru",
        [Project(name="E-Commerce Platform",   category="major"),
         Project(name="Inventory System",       category="mini")]),

    P(2,  "Divya Nair",         "B.Tech", 9.1, 2.0,
        ["Python","Java","SQL","Data Structures","Spring Boot","Git"],
        ["AWS"], "Bengaluru",
        [Project(name="Banking App Backend",   category="college_major"),
         Project(name="REST API Gateway",       category="mini")]),

    P(3,  "Suresh Iyer",        "M.Tech", 8.6, 4.5,
        ["Python","Java","SQL","Data Structures","Kubernetes","Linux"],
        ["AWS","Azure"], "Bengaluru",
        [Project(name="ML Pipeline System",    category="major"),
         Project(name="CI/CD Automation",       category="college_major")]),

    P(4,  "Priya Chakraborty",  "B.Tech", 8.3, 2.5,
        ["Python","Java","SQL","Data Structures","Django","PostgreSQL"],
        ["AWS"], "Bengaluru",
        [Project(name="Job Portal App",         category="college_major"),
         Project(name="DB Optimisation Study",  category="mini")]),

    P(5,  "Vikram Sinha",       "B.E.",   8.0, 1.5,
        ["Python","Java","SQL","Data Structures","Flask","MongoDB"],
        ["AWS"], "Bengaluru",
        [Project(name="Task Manager API",       category="college_major")]),

    P(6,  "Rohit Gupta",        "B.Tech", 7.8, 1.0,
        ["Python","Java","SQL","Data Structures","Node.js","Git"],
        ["AWS"], "Bengaluru",
        [Project(name="Student Portal",         category="college_major")]),

    # ── Borderline / Should be WAIT LIST ─────────────────────────────────────
    P(7,  "Kavya Menon",        "B.Tech", 7.8, 1.0,
        ["Python","SQL","Data Structures","React"],          # missing Java
        ["AWS"], "Bengaluru",
        [Project(name="HR Dashboard",           category="college_major")]),

    P(8,  "Pooja Reddy",        "B.Tech", 7.6, 1.0,
        ["Python","Java","SQL","Data Structures"],
        [],      "Bengaluru",                               # no cert (cert not mandatory)
        [Project(name="Chat Application",       category="mini")]),

    P(9,  "Manish Tiwari",      "M.Tech", 8.5, 3.0,
        ["Python","Java","SQL","Data Structures","TensorFlow"],
        ["AWS"], "Mumbai",                                  # wrong city → CSP fail
        [Project(name="Image Classifier",       category="major"),
         Project(name="NLP Sentiment Tool",     category="college_major")]),

    # ── Ineligible — wrong degree ─────────────────────────────────────────────
    P(10, "Shreya Bose",        "B.Sc",   8.2, 2.0,
        ["Python","Java","SQL","Data Structures"],
        ["AWS"], "Bengaluru",
        [Project(name="Data Analysis Report",   category="college_major")]),

    P(11, "Arjun Das",          "BCA",    7.9, 1.5,
        ["Python","Java","SQL","Data Structures","React"],
        ["AWS"], "Bengaluru",
        [Project(name="Library System",         category="college_major")]),

    # ── Ineligible — low CGPA ────────────────────────────────────────────────
    P(12, "Kiran Pillai",       "B.Tech", 6.8, 2.0,
        ["Python","Java","SQL","Data Structures"],
        ["AWS"], "Bengaluru",
        [Project(name="Quiz App",               category="mini")]),

    P(13, "Nandita Roy",        "B.Tech", 7.2, 1.0,
        ["Python","Java","SQL","Data Structures"],
        ["AWS"], "Bengaluru",
        [Project(name="Hospital System",        category="college_major")]),

    # ── Ineligible — insufficient experience ────────────────────────────────
    P(14, "Aryan Joshi",        "B.Tech", 8.1, 0.0,   # fresher
        ["Python","Java","SQL","Data Structures"],
        ["AWS"], "Bengaluru",
        [Project(name="College ERP",            category="college_major")]),

    P(15, "Riya Kapoor",        "B.Tech", 7.9, 0.5,   # only 0.5 yr
        ["Python","Java","SQL","Data Structures"],
        ["AWS"], "Bengaluru",
        [Project(name="Weather App",            category="mini")]),

    # ── Ineligible — missing required skills ─────────────────────────────────
    P(16, "Siddharth Rao",      "B.Tech", 8.0, 1.5,
        ["Python","SQL","React","Node.js"],               # missing Java + Data Structures
        ["AWS"], "Bengaluru",
        [Project(name="Food Delivery Frontend", category="college_major")]),

    P(17, "Ananya Mathur",      "B.Tech", 8.4, 2.0,
        ["Python","Django","MongoDB","Git"],              # missing Java, SQL, Data Structures
        ["AWS"], "Bengaluru",
        [Project(name="Blog Platform",          category="college_major")]),

    # ── Wildcard — good but remote location ──────────────────────────────────
    P(18, "Varun Nambiar",      "M.Tech", 9.0, 5.0,
        ["Python","Java","SQL","Data Structures","Kubernetes","Docker"],
        ["AWS","GCP"], "Pune",                            # not Bengaluru → CSP fail
        [Project(name="Distributed Cache",      category="major"),
         Project(name="K8s Autoscaler",         category="college_major")]),
]

# ─── Runner + Display ─────────────────────────────────────────────────────────
GREEN  = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"; CYAN = "\033[96m"
BOLD   = "\033[1m";  RESET  = "\033[0m"

STATUS_CLR = {"Selected": GREEN, "Wait List": YELLOW, "Rejected": RED}

def clr(text, color): return f"{color}{text}{RESET}"

def run():
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  TC1 — Software Development Engineer (SDE)  •  18 Candidates{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

    print(f"{BOLD}Job Requirements{RESET}")
    print(f"  Role     : {JOB.title}")
    print(f"  Degrees  : {', '.join(JOB.required_degrees)}")
    print(f"  Min CGPA : {JOB.min_cgpa}  |  Min Exp : {JOB.min_experience} yr")
    print(f"  Skills   : {', '.join(JOB.required_skills)}")
    print(f"  Certs    : {', '.join(JOB.required_certifications)} (not mandatory)")
    print(f"  Location : {JOB.location}  |  Openings : {JOB.openings}\n")

    result = run_pipeline(JOB, CANDIDATES)

    # ── Summary ──
    s = result["summary"]
    print(f"{BOLD}Pipeline Summary{RESET}")
    print(f"  Total: {s['total']}  |  Eligible: {s['eligible']}  |  CSP-valid: {s['csp_valid']}")
    print(f"  {clr('Selected: ' + str(s['Selected']), GREEN)}  "
          f"{clr('Wait List: ' + str(s['Wait List']), YELLOW)}  "
          f"{clr('Rejected: ' + str(s['Rejected']), RED)}\n")

    # ── Ranked table ──
    hdr = f"{'Rank':<5} {'Candidate':<22} {'Status':<10} {'Score':>6} {'Elig':>5} {'CSP':>5} {'FC':>4} {'BC':>4}  Reason"
    print(f"{BOLD}{hdr}{RESET}")
    print("─" * 95)

    by_id = {c["id"]: c for c in result["candidates"]}
    for row in result["ranking"]:
        c   = by_id[row["id"]]
        st  = row["status"]
        sc  = f"{row['score']:.0f}" if row["score"] is not None else "—"
        el  = "✓" if c["eligibility"]["eligible"] else "✗"
        csp = "✓" if c["csp"]["valid"] else "✗"
        fc  = "✓" if c["forward_chaining"]["goal_reached"] else "✗"
        bc  = "✓" if c["backward_chaining"]["proven"] else "✗"
        reason = c["final"]["reasons"][0] if c["final"]["reasons"] else ""
        reason = reason[:48] + "…" if len(reason) > 48 else reason
        color  = STATUS_CLR.get(st, RESET)
        print(f"{row['rank']:<5} {row['name']:<22} {clr(st, color):<19} {sc:>6} "
              f"  {el:>2}    {csp:>2}   {fc:>2}   {bc:>2}  {reason}")

    # ── Stage timing ──
    print(f"\n{BOLD}Algorithm Stages{RESET}")
    for st in result["stages"]:
        print(f"  [{st['algorithm']:40s}]  {st['ms']:6.1f} ms  — {st['summary'][:70]}")

    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}\n")

if __name__ == "__main__":
    run()
