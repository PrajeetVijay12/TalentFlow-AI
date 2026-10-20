"""Demo test-case loader.

POST /api/testcase/{n}   (n = 1, 2, or 3)

Clears the signed-in user's candidates, sets the job, inserts all
candidates directly into the DB (no file upload needed), runs the
full pipeline, and saves the result so the frontend shows it instantly.
"""
from __future__ import annotations

import hashlib
import time

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse

from backend.api.auth_routes import current_user, COOKIE
from backend.models.schemas import CandidateProfile, JobRequirements, Project
from backend.services import auth, database as db
from backend.services.pipeline import run_pipeline

router = APIRouter(prefix="/api")


# ── helpers ──────────────────────────────────────────────────────────────────
def _p(name, degree, cgpa, exp, skills, certs, location, projects=None):
    return CandidateProfile(
        filename=f"{name.replace(' ', '_').lower()}.pdf",
        name=name, degree=degree, cgpa=cgpa, experience=exp,
        skills=skills, certifications=certs, location=location,
        projects=projects or [Project(name="Academic Project", category="mini")],
    )


# ── TC 1 — SDE ───────────────────────────────────────────────────────────────
_TC1_JOB = JobRequirements(
    title="Software Development Engineer",
    required_degrees=["B.Tech", "M.Tech", "B.E.", "M.E."],
    min_cgpa=7.5, min_experience=1.0,
    required_skills=["Python", "Java", "SQL", "Data Structures"],
    required_certifications=["AWS"],
    certifications_mandatory=False, skills_mandatory=True,
    location="Bengaluru", openings=3,
)

_TC1_CANDIDATES = [
    _p("Aakash Sharma",     "B.Tech", 8.9, 3.0, ["Python","Java","SQL","Data Structures","Docker","React"],     ["AWS"], "Bengaluru",
       [Project(name="E-Commerce Platform",category="major"), Project(name="Inventory System",category="mini")]),
    _p("Divya Nair",        "B.Tech", 9.1, 2.0, ["Python","Java","SQL","Data Structures","Spring Boot","Git"],  ["AWS"], "Bengaluru",
       [Project(name="Banking App Backend",category="college_major"), Project(name="REST API Gateway",category="mini")]),
    _p("Suresh Iyer",       "M.Tech", 8.6, 4.5, ["Python","Java","SQL","Data Structures","Kubernetes","Linux"], ["AWS","Azure"], "Bengaluru",
       [Project(name="ML Pipeline System",category="major"), Project(name="CI/CD Automation",category="college_major")]),
    _p("Priya Chakraborty", "B.Tech", 8.3, 2.5, ["Python","Java","SQL","Data Structures","Django","PostgreSQL"], ["AWS"], "Bengaluru",
       [Project(name="Job Portal App",category="college_major"), Project(name="DB Optimisation Study",category="mini")]),
    _p("Vikram Sinha",      "B.E.",   8.0, 1.5, ["Python","Java","SQL","Data Structures","Flask","MongoDB"],    ["AWS"], "Bengaluru",
       [Project(name="Task Manager API",category="college_major")]),
    _p("Rohit Gupta",       "B.Tech", 7.8, 1.0, ["Python","Java","SQL","Data Structures","Node.js","Git"],      ["AWS"], "Bengaluru",
       [Project(name="Student Portal",category="college_major")]),
    _p("Kavya Menon",       "B.Tech", 7.8, 1.0, ["Python","SQL","Data Structures","React"],     ["AWS"], "Bengaluru",    # missing Java
       [Project(name="HR Dashboard",category="college_major")]),
    _p("Pooja Reddy",       "B.Tech", 7.6, 1.0, ["Python","Java","SQL","Data Structures"],       [],     "Bengaluru",    # no cert
       [Project(name="Chat Application",category="mini")]),
    _p("Manish Tiwari",     "M.Tech", 8.5, 3.0, ["Python","Java","SQL","Data Structures","TensorFlow"], ["AWS"], "Mumbai",   # wrong city
       [Project(name="Image Classifier",category="major"), Project(name="NLP Sentiment Tool",category="college_major")]),
    _p("Shreya Bose",       "B.Sc",   8.2, 2.0, ["Python","Java","SQL","Data Structures"],      ["AWS"], "Bengaluru"),  # wrong degree
    _p("Arjun Das",         "BCA",    7.9, 1.5, ["Python","Java","SQL","Data Structures","React"], ["AWS"], "Bengaluru"), # wrong degree
    _p("Kiran Pillai",      "B.Tech", 6.8, 2.0, ["Python","Java","SQL","Data Structures"],      ["AWS"], "Bengaluru"),  # low CGPA
    _p("Nandita Roy",       "B.Tech", 7.2, 1.0, ["Python","Java","SQL","Data Structures"],      ["AWS"], "Bengaluru"),  # low CGPA
    _p("Aryan Joshi",       "B.Tech", 8.1, 0.0, ["Python","Java","SQL","Data Structures"],      ["AWS"], "Bengaluru",   # fresher
       [Project(name="College ERP",category="college_major")]),
    _p("Riya Kapoor",       "B.Tech", 7.9, 0.5, ["Python","Java","SQL","Data Structures"],      ["AWS"], "Bengaluru"),  # 0.5yr < 1yr
    _p("Siddharth Rao",     "B.Tech", 8.0, 1.5, ["Python","SQL","React","Node.js"],             ["AWS"], "Bengaluru"),  # missing Java + DS
    _p("Ananya Mathur",     "B.Tech", 8.4, 2.0, ["Python","Django","MongoDB","Git"],            ["AWS"], "Bengaluru"),  # missing Java, SQL, DS
    _p("Varun Nambiar",     "M.Tech", 9.0, 5.0, ["Python","Java","SQL","Data Structures","Kubernetes","Docker"], ["AWS","GCP"], "Pune",  # Pune not Bengaluru
       [Project(name="Distributed Cache",category="major"), Project(name="K8s Autoscaler",category="college_major")]),
]

# ── TC 2 — Hardware Technician ────────────────────────────────────────────────
_TC2_JOB = JobRequirements(
    title="Hardware Technician",
    required_degrees=["Diploma", "B.Tech", "B.E."],
    min_cgpa=6.0, min_experience=0.5,
    required_skills=["Hardware Repair", "Networking", "Troubleshooting"],
    required_certifications=["CCNA"],
    certifications_mandatory=False, skills_mandatory=True,
    location=None, openings=3,
    weights={"skills": 0.35, "experience": 0.35, "projects": 0.15, "certifications": 0.15},
    thresholds={"selected": 75, "waitlist": 55},
)

_TC2_CANDIDATES = [
    _p("Ramesh Naidu",     "Diploma", 7.8, 3.0, ["Hardware Repair","Networking","Troubleshooting","Circuit Testing","Soldering"],   ["CCNA"], "Chennai",
       [Project(name="LAN Setup for School Lab",category="college_major"), Project(name="Server Rack Installation",category="mini")]),
    _p("Lakshmi Varma",    "B.Tech",  7.2, 2.0, ["Hardware Repair","Networking","Troubleshooting","Linux","Oscilloscope"],           ["CCNA"], "Hyderabad",
       [Project(name="Network Monitoring Tool",category="college_major"), Project(name="PCB Fault Detection System",category="major")]),
    _p("Dinesh Kumar",     "Diploma", 7.0, 4.0, ["Hardware Repair","Networking","Troubleshooting","PLC Programming","CCTV Setup"],   ["CCNA","Security+"], "Coimbatore",
       [Project(name="Factory Floor Network",category="major"), Project(name="CCTV Integration",category="mini")]),
    _p("Meera Pillai",     "B.E.",    7.5, 2.5, ["Hardware Repair","Networking","Troubleshooting","Wireless Config","VoIP"],         ["CCNA"], "Kochi",
       [Project(name="Office Wi-Fi Rollout",category="college_major"), Project(name="VoIP PBX Setup",category="mini")]),
    _p("Sunil Patil",      "Diploma", 6.8, 1.5, ["Hardware Repair","Networking","Troubleshooting","Soldering","UPS Maintenance"],    ["CCNA"], "Pune",
       [Project(name="Server UPS Upgrade",category="mini")]),
    _p("Geetha Rajan",     "Diploma", 6.5, 0.5, ["Hardware Repair","Networking","Troubleshooting"],       [],     "Chennai",         # no cert
       [Project(name="Classroom Projector Setup",category="mini")]),
    _p("Anil Sharma",      "B.Tech",  6.2, 1.0, ["Hardware Repair","Troubleshooting","Soldering","Circuit Testing"], ["CCNA"], "Delhi",  # missing Networking
       [Project(name="Embedded Sensor Module",category="mini")]),
    _p("Farhan Sheikh",    "Diploma", 6.1, 0.5, ["Hardware Repair","Networking","Troubleshooting"],                  ["CCNA"], "Mumbai",
       [Project(name="Cable Tray Installation",category="mini")]),
    _p("Tanya Mehta",      "B.Sc",    7.0, 2.0, ["Hardware Repair","Networking","Troubleshooting"],                  ["CCNA"], "Bengaluru"),  # wrong degree
    _p("Vijay Nair",       "B.Com",   6.5, 1.0, ["Hardware Repair","Networking","Troubleshooting"],                  ["CCNA"], "Chennai"),    # wrong degree
    _p("Kavitha Sundaram", "Diploma", 5.2, 1.5, ["Hardware Repair","Networking","Troubleshooting"],                  ["CCNA"], "Coimbatore", # low CGPA
       [Project(name="Computer Lab Wiring",category="mini")]),
    _p("Raju Krishnan",    "B.Tech",  5.8, 2.0, ["Hardware Repair","Networking","Troubleshooting"],                  ["CCNA"], "Hyderabad"),  # low CGPA
    _p("Preethi Rao",      "Diploma", 7.5, 0.0, ["Hardware Repair","Networking","Troubleshooting"],                  ["CCNA"], "Chennai",     # fresher
       [Project(name="Final Year Lab Setup",category="college_major")]),
    _p("Mohan Babu",       "Diploma", 6.8, 1.5, ["Circuit Testing","Soldering","UPS Maintenance"],                   ["CCNA"], "Chennai"),    # no core skills
    _p("Swetha Iyer",      "B.Tech",  7.1, 1.0, ["Linux","Python","Networking"],                                     [],      "Bengaluru",   # missing HW Repair + Troubleshoot
       [Project(name="Network Traffic Analyser",category="mini")]),
    _p("Harish Balan",     "B.E.",    6.9, 2.5, ["Hardware Repair","CCTV Setup","UPS Maintenance"],                  ["CCNA"], "Madurai"),    # missing Networking + Troubleshoot
]

# ── TC 3 — Content Writer ─────────────────────────────────────────────────────
_TC3_JOB = JobRequirements(
    title="Content Writer",
    required_degrees=["B.A.", "B.Sc", "B.Com", "B.Tech"],
    degrees_equivalent=False,
    min_cgpa=6.5, min_experience=0.5,
    required_skills=["Content Writing", "SEO", "Research"],
    required_certifications=["Scrum"],
    certifications_mandatory=False, skills_mandatory=True,
    location="Mumbai", openings=2,
    weights={"skills": 0.45, "experience": 0.25, "projects": 0.20, "certifications": 0.10},
    thresholds={"selected": 80, "waitlist": 60},
)

_TC3_CANDIDATES = [
    _p("Aisha Khan",       "B.A.",    8.2, 3.0, ["Content Writing","SEO","Research","Copywriting","WordPress","Social Media"], ["Scrum"], "Mumbai",
       [Project(name="Brand Blog Campaign",category="major"), Project(name="SEO Audit Report",category="college_major")]),
    _p("Sneha Patil",      "B.Com",   7.8, 2.0, ["Content Writing","SEO","Research","Email Marketing","Google Analytics"],     ["Scrum"], "Mumbai",
       [Project(name="E-Commerce Content Strategy",category="college_major"), Project(name="Newsletter Series",category="mini")]),
    _p("Riya Sharma",      "B.Sc",    8.0, 2.5, ["Content Writing","SEO","Research","Video Scripting","WordPress","Proofreading"], ["Scrum"], "Mumbai",
       [Project(name="Science Magazine Column",category="college_major"), Project(name="YouTube Script Series",category="mini")]),
    _p("Deepika Joshi",    "B.A.",    7.0, 1.0, ["Content Writing","SEO","Research","Copywriting"],                            [],      "Mumbai",  # no cert
       [Project(name="Travel Blog",category="college_major")]),
    _p("Aarav Mehta",      "B.Tech",  7.5, 0.5, ["Content Writing","SEO","Research","Technical Writing"],                      ["Scrum"], "Mumbai",
       [Project(name="Tech Tutorial Series",category="mini")]),
    _p("Sunita Rao",       "B.A.",    6.8, 1.5, ["Content Writing","SEO","Research","Editing"],                                ["Scrum"], "Pune",    # wrong city
       [Project(name="Lifestyle Brand Blog",category="college_major")]),
    _p("Mihir Desai",      "B.Com",   7.2, 1.0, ["Content Writing","Research","Copywriting","Social Media"],                   ["Scrum"], "Mumbai",  # missing SEO
       [Project(name="Finance Blog",category="mini")]),
    _p("Pooja Dubey",      "Diploma", 7.5, 1.5, ["Content Writing","SEO","Research","Blogging"],                               ["Scrum"], "Mumbai",  # wrong degree
       [Project(name="Fashion Blog Portfolio",category="college_major")]),
    _p("Ritesh Kumar",     "MCA",     8.0, 2.0, ["Content Writing","SEO","Research","WordPress"],                              ["Scrum"], "Mumbai",  # wrong degree
       [Project(name="Tech Blog Platform",category="college_major")]),
    _p("Nandini Ghosh",    "B.A.",    5.9, 2.0, ["Content Writing","SEO","Research","Creative Writing"],                       ["Scrum"], "Mumbai",  # low CGPA
       [Project(name="Storytelling Portfolio",category="college_major")]),
    _p("Tushar Bhatia",    "B.Com",   6.3, 1.0, ["Content Writing","SEO","Research"],                                         [],      "Mumbai"),   # low CGPA
    _p("Kavya Singh",      "B.A.",    7.6, 0.0, ["Content Writing","SEO","Research","Social Media"],                           ["Scrum"], "Mumbai",  # fresher
       [Project(name="College Magazine Editor",category="college_major")]),
    _p("Preeti Iyer",      "B.Sc",    7.0, 0.3, ["Content Writing","SEO","Research"],                                         [],      "Mumbai"),   # 0.3yr < 0.5yr
    _p("Rahul Pandey",     "B.A.",    7.2, 1.0, ["Copywriting","WordPress","Social Media","Email Marketing"],                  ["Scrum"], "Mumbai"),  # no core skills
    _p("Anjali Varma",     "B.Com",   7.5, 2.0, ["Graphic Design","Video Editing","Photography"],                             [],      "Mumbai",   # different skills
       [Project(name="Brand Visual Identity",category="college_major")]),
    _p("Karan Oberoi",     "Diploma", 5.5, 0.0, ["Blogging","WordPress"],                                                     [],      "Delhi"),   # multiple fails
    _p("Shalini Das",      "B.A.",    8.5, 4.0, ["Content Writing","SEO","Research","Copywriting","Brand Strategy"],           ["Scrum"], "Kolkata", # wrong city
       [Project(name="Multinational Brand Campaign",category="major"), Project(name="SEO Content Playbook",category="college_major")]),
]

_TC_DATA = {
    1: (_TC1_JOB, _TC1_CANDIDATES),
    2: (_TC2_JOB, _TC2_CANDIDATES),
    3: (_TC3_JOB, _TC3_CANDIDATES),
}

_TC_LABELS = {
    1: "TC1 — Software Development Engineer (18 candidates, Bengaluru)",
    2: "TC2 — Hardware Technician (16 candidates, any city)",
    3: "TC3 — Content Writer (17 candidates, Mumbai)",
}


def _setup_for_user(n: int, uid: int) -> None:
    """Clear existing data, set job, insert candidates — pipeline is left for the browser to trigger."""
    job, template_candidates = _TC_DATA[n]
    db.clear_candidates(uid)
    db.save_job(uid, job)
    for cand in template_candidates:
        sha = hashlib.sha256(f"tc{n}:{cand.name}".encode()).hexdigest()
        db.add_candidate(uid, sha, cand)


def _load_for_user(n: int, uid: int) -> dict:
    """Clear, set job, insert candidates, run pipeline, save run — for the POST endpoint."""
    job, template_candidates = _TC_DATA[n]
    db.clear_candidates(uid)
    db.save_job(uid, job)
    for cand in template_candidates:
        sha = hashlib.sha256(f"tc{n}:{cand.name}".encode()).hexdigest()
        db.add_candidate(uid, sha, cand)
    loaded = db.list_candidates(uid)
    result = run_pipeline(job, loaded)
    db.save_run(uid, result)
    return result


# ── POST endpoint (used by old terminal scripts) ─────────────────────────────
@router.post("/testcase/{n}", dependencies=[Depends(current_user)])
def load_testcase(n: int, user: dict = Depends(current_user)):
    if n not in _TC_DATA:
        raise HTTPException(400, detail="Test case must be 1, 2, or 3.")

    if n not in _TC_DATA:
        raise HTTPException(400, detail="Test case must be 1, 2, or 3.")
    result = _load_for_user(n, user["id"])
    s = result["summary"]
    return {
        "ok": True,
        "label": _TC_LABELS[n],
        "total": s["total"],
        "eligible": s["eligible"],
        "selected": s["Selected"],
        "waitlist": s["Wait List"],
        "rejected": s["Rejected"],
    }


# ── GET /api/testcase/launch/{n}  — browser-friendly one-click loader ─────────
# Opens this URL in the browser: auto-registers/logs in the demo user,
# loads the test case, runs the pipeline, then redirects to /shortlist.
TC_DEMO_EMAIL    = "tc_demo@talentflow.ai"
TC_DEMO_PASSWORD = "TcDemo@99"
TC_DEMO_NAME     = "TC Demo"

@router.get("/testcase/launch/{n}")
def launch_testcase(n: int, response: Response):
    if n not in _TC_DATA:
        raise HTTPException(400, detail="Test case must be 1, 2, or 3.")

    # Register or get existing demo user
    existing = db.user_by_email(TC_DEMO_EMAIL)
    if existing:
        uid = existing["id"]
    else:
        uid = db.create_user(TC_DEMO_EMAIL, TC_DEMO_NAME, auth.hash_password(TC_DEMO_PASSWORD))

    # Load candidates + job (no pipeline run — the browser triggers it with the animation)
    _setup_for_user(n, uid)

    # Set a session cookie so the browser is logged in as this user
    token, token_hash = auth.new_token()
    db.create_session(uid, token_hash, time.time() + auth.SESSION_SECONDS)
    # Redirect to /pipeline?autorun=1 — the pipeline page detects this and starts the
    # workflow animation automatically, then navigates to results when done.
    redirect = RedirectResponse(url="/pipeline?autorun=1", status_code=302)
    redirect.set_cookie(COOKIE, token, max_age=auth.SESSION_SECONDS,
                        httponly=True, samesite="lax", path="/")
    return redirect
