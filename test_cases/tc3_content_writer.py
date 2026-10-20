"""
TC3 — Content Writer
=====================
17 candidates with varied writing/digital-media profiles.
Run from the project root:  python test_cases/tc3_content_writer.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.models.schemas import CandidateProfile, JobRequirements, Project
from backend.services.pipeline import run_pipeline

# ─── Job Definition ──────────────────────────────────────────────────────────
JOB = JobRequirements(
    title="Content Writer",
    required_degrees=["B.A.", "B.Sc", "B.Com", "B.Tech"],
    degrees_equivalent=False,
    min_cgpa=6.5,
    min_experience=0.5,
    required_skills=["Content Writing", "SEO", "Research"],
    required_certifications=["Scrum"],       # soft / nice-to-have
    certifications_mandatory=False,
    skills_mandatory=True,
    location="Mumbai",
    openings=2,
    weights={"skills": 0.45, "experience": 0.25, "projects": 0.20, "certifications": 0.10},
    thresholds={"selected": 80, "waitlist": 60},
)

# ─── Candidates ──────────────────────────────────────────────────────────────
def P(id_, name, degree, cgpa, exp, skills, certs, location, projects=None):
    return CandidateProfile(
        id=id_, filename=f"{name.replace(' ','_').lower()}.pdf",
        name=name, degree=degree, cgpa=cgpa, experience=exp,
        skills=skills, certifications=certs, location=location,
        projects=projects or [Project(name="Writing Portfolio", category="mini")],
    )

CANDIDATES = [
    # ── Strong / Should be SELECTED ──────────────────────────────────────────
    P(1,  "Aisha Khan",          "B.A.",   8.2, 3.0,
        ["Content Writing","SEO","Research","Copywriting","WordPress","Social Media"],
        ["Scrum"], "Mumbai",
        [Project(name="Brand Blog Campaign",         category="major"),
         Project(name="SEO Audit Report",             category="college_major")]),

    P(2,  "Sneha Patil",         "B.Com",  7.8, 2.0,
        ["Content Writing","SEO","Research","Email Marketing","Google Analytics"],
        ["Scrum"], "Mumbai",
        [Project(name="E-Commerce Content Strategy", category="college_major"),
         Project(name="Newsletter Series",            category="mini")]),

    P(3,  "Riya Sharma",         "B.Sc",   8.0, 2.5,
        ["Content Writing","SEO","Research","Video Scripting","WordPress","Proofreading"],
        ["Scrum"], "Mumbai",
        [Project(name="Science Magazine Column",     category="college_major"),
         Project(name="YouTube Script Series",       category="mini")]),

    # ── Borderline / Should be WAIT LIST ─────────────────────────────────────
    P(4,  "Deepika Joshi",       "B.A.",   7.0, 1.0,
        ["Content Writing","SEO","Research","Copywriting"],
        [],      "Mumbai",                              # no cert (not mandatory)
        [Project(name="Travel Blog",                 category="college_major")]),

    P(5,  "Aarav Mehta",         "B.Tech", 7.5, 0.5,
        ["Content Writing","SEO","Research","Technical Writing"],
        ["Scrum"], "Mumbai",
        [Project(name="Tech Tutorial Series",        category="mini")]),

    P(6,  "Sunita Rao",          "B.A.",   6.8, 1.5,
        ["Content Writing","SEO","Research","Editing"],
        ["Scrum"], "Pune",                              # wrong city → CSP fail
        [Project(name="Lifestyle Brand Blog",        category="college_major")]),

    P(7,  "Mihir Desai",         "B.Com",  7.2, 1.0,
        ["Content Writing","Research","Copywriting","Social Media"],  # missing SEO
        ["Scrum"], "Mumbai",
        [Project(name="Finance Blog",                category="mini")]),

    # ── Ineligible — wrong degree ─────────────────────────────────────────────
    P(8,  "Pooja Dubey",         "Diploma", 7.5, 1.5,
        ["Content Writing","SEO","Research","Blogging"],
        ["Scrum"], "Mumbai",
        [Project(name="Fashion Blog Portfolio",      category="college_major")]),

    P(9,  "Ritesh Kumar",        "MCA",    8.0, 2.0,
        ["Content Writing","SEO","Research","WordPress"],
        ["Scrum"], "Mumbai",
        [Project(name="Tech Blog Platform",          category="college_major")]),

    # ── Ineligible — low CGPA ────────────────────────────────────────────────
    P(10, "Nandini Ghosh",       "B.A.",   5.9, 2.0,
        ["Content Writing","SEO","Research","Creative Writing"],
        ["Scrum"], "Mumbai",
        [Project(name="Storytelling Portfolio",      category="college_major")]),

    P(11, "Tushar Bhatia",       "B.Com",  6.3, 1.0,
        ["Content Writing","SEO","Research"],
        [],      "Mumbai"),

    # ── Ineligible — insufficient experience ─────────────────────────────────
    P(12, "Kavya Singh",         "B.A.",   7.6, 0.0,  # fresher
        ["Content Writing","SEO","Research","Social Media"],
        ["Scrum"], "Mumbai",
        [Project(name="College Magazine Editor",     category="college_major")]),

    P(13, "Preeti Iyer",         "B.Sc",   7.0, 0.3,  # 0.3 yr < 0.5 yr required
        ["Content Writing","SEO","Research"],
        [],      "Mumbai"),

    # ── Ineligible — missing required skills ─────────────────────────────────
    P(14, "Rahul Pandey",        "B.A.",   7.2, 1.0,
        ["Copywriting","WordPress","Social Media","Email Marketing"],   # no core skills
        ["Scrum"], "Mumbai"),

    P(15, "Anjali Varma",        "B.Com",  7.5, 2.0,
        ["Graphic Design","Video Editing","Photography"],                # completely different skills
        [],      "Mumbai",
        [Project(name="Brand Visual Identity",       category="college_major")]),

    # ── Ineligible — two fails together ──────────────────────────────────────
    P(16, "Karan Oberoi",        "Diploma", 5.5, 0.0,
        ["Blogging","WordPress"],
        [],      "Delhi"),

    P(17, "Shalini Das",         "B.A.",   8.5, 4.0,
        ["Content Writing","SEO","Research","Copywriting","Brand Strategy"],
        ["Scrum"], "Kolkata",                           # city mismatch → CSP fail
        [Project(name="Multinational Brand Campaign", category="major"),
         Project(name="SEO Content Playbook",         category="college_major")]),
]

# ─── Runner + Display ────────────────────────────────────────────────────────
GREEN  = "\033[92m"; YELLOW = "\033[93m"; RED = "\033[91m"; CYAN = "\033[96m"
BOLD   = "\033[1m";  RESET  = "\033[0m"
STATUS_CLR = {"Selected": GREEN, "Wait List": YELLOW, "Rejected": RED}

def clr(text, color): return f"{color}{text}{RESET}"

def run():
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}  TC3 — Content Writer  •  17 Candidates{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

    print(f"{BOLD}Job Requirements{RESET}")
    print(f"  Role     : {JOB.title}")
    print(f"  Degrees  : {', '.join(JOB.required_degrees)}")
    print(f"  Min CGPA : {JOB.min_cgpa}  |  Min Exp : {JOB.min_experience} yr")
    print(f"  Skills   : {', '.join(JOB.required_skills)}")
    print(f"  Certs    : {', '.join(JOB.required_certifications)} (not mandatory)")
    print(f"  Location : {JOB.location}  |  Openings : {JOB.openings}\n")

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
