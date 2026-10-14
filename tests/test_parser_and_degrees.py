from backend.algorithms.backward_chaining import backward_chain
from backend.algorithms.bfs import bfs_eligibility
from backend.algorithms.criteria import build_eligibility_tree
from backend.algorithms.csp import solve_csp
from backend.algorithms.forward_chaining import forward_chain
from backend.algorithms.knowledge_base import build_facts, build_rules
from backend.models.schemas import CandidateProfile
from backend.parsing.normalizer import degree_matches
from backend.parsing.resume_parser import parse_resume_text
from tests.helpers import load_samples, sample_job

# Text in the order a two-column PDF produces it: headings first, content scattered afterwards.
SCRAMBLED = """PRAJEET V
ALERTLY ResQ – Emergency Relief Platform
B.E. Computer Science and Engineering
Rajalakshmi Engineering College (2nd Year)
Higher Secondary – 84%
AI Smart Dustbin – Smart Waste Management System
Chennai  |  9363389320  |  vprajeet@gmail.com
GitHub: github.com/Prajeet2k25
SUMMARY
PROJECTS
EDUCATION
ACHIEVEMENTS
TECHNICAL SKILLS
INTERNSHIP EXPERIENCE
DATA ANALYST – G-Tech Computer Solutions (2 Weeks)
Programming: Python, Java, C
• Developed an AI-based system to classify waste
• 3rd Place – Chandigarh Police National Hackathon 2026
PRODUCT DEVELOPER – TIQ World, IITM Research Park (June 2026 – Present)
Pramana – AI-Powered Digital Forensics Platform
"""


# ------------------------------------------------------------ parser
def test_location_is_read_from_the_contact_line():
    c = parse_resume_text(SCRAMBLED, "r.pdf")
    assert c.location == "Chennai"


def test_contact_line_location_does_not_grab_links_or_numbers():
    c = parse_resume_text("Asha K\nasha@mail.com | 9876543210 | github.com/asha\nSkills\nPython\n", "a.pdf")
    assert c.location is None
    c2 = parse_resume_text("Asha K\nPune, Maharashtra | asha@mail.com | 9876543210\n", "a.pdf")
    assert c2.location == "Pune, Maharashtra"


def test_explicit_location_label_still_wins():
    c = parse_resume_text("Asha K\nLocation: Hyderabad\nChennai | asha@mail.com | 9876543210\n", "a.pdf")
    assert c.location == "Hyderabad"


def test_projects_recovered_from_scrambled_layout_without_false_positives():
    c = parse_resume_text(SCRAMBLED, "r.pdf")
    names = [p.name for p in c.projects]
    assert names == ["ALERTLY ResQ", "AI Smart Dustbin", "Pramana"]
    for junk in ("DATA ANALYST", "PRODUCT DEVELOPER", "Higher Secondary", "3rd Place", "B.E. Computer Science and Engineering"):
        assert not any(junk in n for n in names)
    assert any("multi-column" in n for n in c.notes)       # the user is told this was recovered, not read directly


def test_normal_projects_section_is_not_overridden_by_fallback():
    text = "Asha\nProjects\nSmart Home - Major Project: IoT hub\nEducation\nB.Tech\nOther Tool – Some description here\n"
    c = parse_resume_text(text, "a.pdf")
    assert [p.name for p in c.projects] == ["Smart Home"] and c.projects[0].score == 100


def test_sample_resumes_unchanged_by_new_rules():
    by = {c.name: c for c in load_samples()}
    assert by["Rahul Sharma"].location == "Bengaluru" and len(by["Rahul Sharma"].projects) == 2
    assert [p.name for p in by["Priya Nair"].projects] == ["Smart Attendance System"]


# ----------------------------------------------------- B.E. = B.Tech
def test_degree_matching_rules():
    assert degree_matches("B.E.", ["B.Tech"], True)
    assert degree_matches("B.Tech", ["B.E."], True)
    assert degree_matches("M.E.", ["M.Tech"], True)
    assert not degree_matches("B.E.", ["B.Tech"], False)           # exact mode
    assert not degree_matches("B.E.", ["M.Tech"], True)            # bachelor is never a master
    assert not degree_matches("BCA", ["B.Tech"], True)
    assert not degree_matches(None, ["B.Tech"], True) and degree_matches(None, [], True)


def be_candidate():
    return CandidateProfile(id=1, name="Be Student", degree="B.E.", cgpa=8.0, skills=["Python", "Java", "SQL"],
                            experience=2, location="Bengaluru", certifications=["AWS"])


def test_be_candidate_passes_btech_job_by_default_everywhere():
    job, c = sample_job(), be_candidate()
    assert job.degrees_equivalent is True
    assert bfs_eligibility(build_eligibility_tree(job, c))["eligible"]
    assert solve_csp(job, c)["valid"]
    facts, rules = build_facts(job, c), build_rules(job)
    assert forward_chain(facts, rules)["goal_reached"] and backward_chain(facts, rules)["proven"]


def test_be_candidate_rejected_when_exact_match_is_chosen_and_all_stages_agree():
    job, c = sample_job(degrees_equivalent=False), be_candidate()
    report = bfs_eligibility(build_eligibility_tree(job, c))
    assert not report["eligible"] and [k["label"] for k in report["checks"] if k["status"] == "FAIL"] == ["Degree"]
    assert not solve_csp(job, c)["valid"]
    facts, rules = build_facts(job, c), build_rules(job)
    assert not forward_chain(facts, rules)["goal_reached"]
    bc = backward_chain(facts, rules)
    assert not bc["proven"] and "Degree requirement" in bc["failed_requirements"]
