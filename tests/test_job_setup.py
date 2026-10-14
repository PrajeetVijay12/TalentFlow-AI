from backend.services.jd_parser import parse_job_description
from tests.helpers import signed_in_client

JD = """Backend Developer
We are hiring 3 positions in Bangalore. B.E / B.Tech in Computer Science with 7.5 CGPA or above.
Minimum 2 years of experience. Must know Python, Java and SQL; PostgreSQL and Docker are a plus.
AWS certification is mandatory."""


def test_jd_parser_fills_the_criteria():
    r = parse_job_description(JD)["suggestion"]
    assert r["title"] == "Backend Developer"
    assert set(r["required_degrees"]) == {"B.E.", "B.Tech"}
    assert r["min_cgpa"] == 7.5 and r["min_experience"] == 2 and r["openings"] == 3
    assert {"Python", "Java", "SQL", "Docker", "PostgreSQL"} <= set(r["required_skills"])
    assert r["required_certifications"] == ["AWS"] and r["certifications_mandatory"] is True
    assert r["location"] == "Bengaluru"            # 'Bangalore' normalized


def test_jd_parser_reports_what_it_could_not_find():
    out = parse_job_description("We need a Data Analyst who knows Excel.")
    assert "skills" in out["found"] and "location" in out["not_found"] and "minimum CGPA" in out["not_found"]


def test_fresher_means_zero_experience():
    assert parse_job_description("Freshers welcome. Python required, B.Tech.")["suggestion"]["min_experience"] == 0


def test_options_and_parse_endpoints():
    c = signed_in_client()
    o = c.get("/api/options").json()
    assert "B.Tech" in o["degrees"] and "Python" in o["skills"] and "AWS" in o["certifications"] and "Bengaluru" in o["locations"]
    assert c.post("/api/job/parse", json={"text": JD}).json()["suggestion"]["min_cgpa"] == 7.5
    assert c.post("/api/job/parse", json={"text": "hi"}).status_code == 422
