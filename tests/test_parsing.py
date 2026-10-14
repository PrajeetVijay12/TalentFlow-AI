import pytest

from backend.parsing.normalizer import (canonical_cert, canonical_skill, find_degree, find_skills_in_text,
                                        location_key, normalize_degree)
from backend.parsing.resume_parser import parse_resume_text
from backend.parsing.text_extractor import ParseError, extract_text
from tests.helpers import SAMPLES


@pytest.mark.parametrize("raw", ["B.Tech", "BTech", "btech", "b.tech", "Bachelor of Technology", "B. Tech"])
def test_degree_variants_normalize_to_same_value(raw):
    assert normalize_degree(raw) == "B.Tech"


def test_other_degrees():
    assert find_degree("Master of Computer Applications") == "MCA"
    assert find_degree("BCA, Christ University") == "BCA"
    assert find_degree("no degree here") is None


def test_skill_case_insensitive():
    assert canonical_skill("python") == canonical_skill("PYTHON") == "Python"
    assert canonical_skill("postgres") == "PostgreSQL"


def test_skill_scan_does_not_confuse_java_and_javascript():
    assert find_skills_in_text("I know JavaScript only") == ["JavaScript"]
    assert find_skills_in_text("Java and MySQL") == ["Java", "MySQL"]


def test_cert_and_location_normalization():
    assert canonical_cert("AWS Certified Solutions Architect") == "AWS"
    assert location_key("Bangalore, Karnataka") == location_key("Bengaluru") == "bengaluru"


def test_parse_text_example():
    text = """Rahul
rahul@example.com | +91 98765 43210
Education
B.Tech in Computer Science
CGPA: 8.6/10
Skills
Python, Java, SQL
Experience
2 years of experience as a developer
Projects
Hospital Management System - Major Project
Certifications
AWS Certified Solutions Architect
"""
    c = parse_resume_text(text, "rahul.pdf")
    assert c.name == "Rahul"
    assert c.email == "rahul@example.com"
    assert c.degree == "B.Tech" and c.cgpa == 8.6
    assert c.skills == ["Python", "Java", "SQL"]
    assert c.experience == 2
    assert c.projects[0].name == "Hospital Management System" and c.projects[0].score == 100
    assert c.certifications == ["AWS"]


def test_experience_from_date_range():
    c = parse_resume_text("Asha\nExperience\nDeveloper, Jan 2021 - Dec 2022\n", "a.pdf")
    assert c.experience == 2.0


def test_project_categories():
    c = parse_resume_text("Asha\nProjects\nA - Mini Project\nB - College Major Project\nC - Major Project\n", "a.pdf")
    assert [p.score for p in c.projects] == [60, 80, 100]


def test_missing_fields_reported():
    c = parse_resume_text("Asha\nSkills\nPython\n", "a.pdf")
    assert "degree" in c.missing_fields and "cgpa" in c.missing_fields


def test_real_pdf_and_docx_samples_parse():
    pdf = next(SAMPLES.glob("*.pdf"))
    docx = next(SAMPLES.glob("*.docx"))
    for p in (pdf, docx):
        c = parse_resume_text(extract_text(p.name, p.read_bytes()), p.name)
        assert c.email and c.degree == "B.Tech" and c.cgpa


def test_corrupted_files_raise_parse_error():
    with pytest.raises(ParseError):
        extract_text("x.pdf", b"%PDF-1.4 this is not really a pdf")
    with pytest.raises(ParseError):
        extract_text("x.docx", b"PK\x03\x04garbage")
    with pytest.raises(ParseError):
        extract_text("x.txt", b"hello")
