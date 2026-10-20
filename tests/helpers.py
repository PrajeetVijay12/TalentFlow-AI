"""Shared test helpers: the sample job and the parsed sample resumes."""
from pathlib import Path

from backend.models.schemas import JobRequirements
from backend.parsing.resume_parser import parse_resume_text
from backend.parsing.text_extractor import extract_text

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "sample_data" / "resumes"


def sample_job(**overrides) -> JobRequirements:
    data = dict(title="Software Engineer", required_degrees=["B.Tech"], min_cgpa=7.5, min_experience=1,
                required_skills=["Python", "Java", "SQL"], required_certifications=["AWS"], location="Bengaluru",
                openings=2)
    data.update(overrides)
    return JobRequirements(**data)


def load_samples():
    """Load the 7 unique-candidate PDF resumes for unit tests (excludes .docx duplicates)."""
    out = []
    for i, p in enumerate(sorted(SAMPLES.glob("*.pdf")), start=1):
        c = parse_resume_text(extract_text(p.name, p.read_bytes()), p.name)
        c.id = i
        out.append(c)
    return out


def signed_in_client(name: str = "Test Recruiter"):
    """A TestClient that has registered a brand-new user (the session cookie is kept automatically)."""
    import uuid

    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    r = client.post("/api/auth/register", json={"name": name, "email": f"{uuid.uuid4().hex[:10]}@example.com", "password": "Str0ng-pass!"})
    assert r.status_code == 200, r.text
    return client
