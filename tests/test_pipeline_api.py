import io

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import database as db
from backend.services.pipeline import run_pipeline
from tests.helpers import SAMPLES, load_samples, sample_job, signed_in_client


def by_name(result):
    return {c["name"]: c for c in result["candidates"]}


def test_pipeline_end_to_end_on_samples():
    r = run_pipeline(sample_job(), load_samples())
    c = by_name(r)
    assert c["Rahul Sharma"]["final"]["status"] == "Selected"
    assert c["Priya Nair"]["final"]["status"] == "Selected"
    assert c["Sneha Iyer"]["final"]["status"] == "Wait List"
    assert c["Arjun Mehta"]["eligibility"]["failed"] == ["Skill: SQL"]          # missing skill
    assert c["Neha Verma"]["eligibility"]["failed"] == ["Experience"]           # not enough experience
    assert set(c["Karan Singh"]["eligibility"]["failed"]) == {"Degree", "CGPA"} # degree / CGPA
    assert c["Vikram Rao"]["eligibility"]["eligible"] and not c["Vikram Rao"]["csp"]["valid"]  # location
    assert c["Vikram Rao"]["final"]["status"] == "Rejected"
    assert [x["rank"] for x in r["ranking"]] == list(range(1, 8))
    assert r["alpha_beta"]["nodes_pruned"] > 0


def test_all_algorithms_ran_and_agree():
    r = run_pipeline(sample_job(), load_samples())
    for c in r["candidates"]:
        assert c["eligibility"]["agree"]  # BFS and DFS give the same verdict
        assert c["forward_chaining"]["goal_reached"] == c["backward_chaining"]["proven"] == c["final"]["csp_valid"]
    assert r["local_search"]["final_objective"] >= r["local_search"]["initial_objective"]


def test_thresholds_are_configurable():
    r = run_pipeline(sample_job(thresholds={"selected": 99, "waitlist": 90}), load_samples())
    c = by_name(r)
    assert c["Rahul Sharma"]["final"]["status"] == "Selected"   # 100 >= 99
    assert c["Priya Nair"]["final"]["status"] == "Rejected"     # 86 < 90
    assert c["Sneha Iyer"]["final"]["status"] == "Rejected"     # 82 < 90


def test_openings_limit_selection():
    r = run_pipeline(sample_job(openings=1), load_samples())
    c = by_name(r)
    assert c["Rahul Sharma"]["final"]["status"] == "Selected"
    assert c["Priya Nair"]["final"]["status"] == "Wait List"  # score 86 >= 85 but the only opening is taken


def test_pipeline_requires_candidates():
    with pytest.raises(ValueError):
        run_pipeline(sample_job(), [])


# ------------------------------------------------------------------- API
@pytest.fixture()
def client():
    db.init_db()
    return signed_in_client()


def test_api_job_validation(client):
    assert client.put("/api/job", json={"min_cgpa": 15}).status_code == 422
    assert client.put("/api/job", json={"required_skills": []}).status_code == 422
    r = client.put("/api/job", json={"thresholds": {"selected": 60, "waitlist": 80}})
    assert r.status_code == 422 and "threshold" in str(r.json()["detail"]).lower()
    ok = client.put("/api/job", json={"required_skills": ["python", "SQL"], "required_degrees": ["BTech"], "location": "Bengaluru"})
    assert ok.status_code == 200 and ok.json()["required_skills"] == ["Python", "SQL"]
    assert ok.json()["required_degrees"] == ["B.Tech"]


def test_api_run_without_resumes_is_a_clear_error(client):
    r = client.post("/api/run")
    assert r.status_code == 400 and "No resumes" in r.json()["detail"]
    assert client.post("/api/resumes").status_code in (400, 422)


def test_api_upload_errors_and_duplicates(client):
    pdf = next(SAMPLES.glob("*.pdf"))
    files = [("files", ("a.pdf", pdf.read_bytes(), "application/pdf")),
             ("files", ("a_copy.pdf", pdf.read_bytes(), "application/pdf")),
             ("files", ("bad.pdf", b"%PDF-1.4 junk", "application/pdf")),
             ("files", ("fake.docx", b"not a zip", "application/octet-stream")),
             ("files", ("notes.txt", b"hello", "text/plain")),
             ("files", ("../../evil.pdf", b"", "application/pdf")),
             ("files", ("big.pdf", b"%PDF" + b"0" * (6 * 1024 * 1024), "application/pdf"))]
    res = client.post("/api/resumes", files=files).json()["results"]
    status = [r["status"] for r in res]
    assert status == ["ok", "duplicate", "error", "error", "error", "error", "error"]
    assert "corrupted" in res[2]["message"].lower()
    assert "larger" in res[6]["message"]
    assert "/" not in res[5]["filename"]  # sanitized
    assert len(client.get("/api/candidates").json()) == 1


def test_api_full_flow_with_samples(client):
    loaded = client.post("/api/samples/load").json()["results"]
    assert [r["status"] for r in loaded].count("ok") == 10  # 7 PDFs + 3 DOCX variants
    r = client.post("/api/run")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["Selected"] == 2 and body["summary"]["total"] == 10
    assert client.get("/api/run/latest").json()["summary"] == body["summary"]
    assert len(client.get("/api/algorithms").json()["table"]) == 9


def test_api_edit_candidate_changes_result(client):
    client.post("/api/samples/load")
    karan = next(c for c in client.get("/api/candidates").json() if c["name"] == "Karan Singh")
    r = client.put(f"/api/candidates/{karan['id']}", json={"degree": "B.Tech", "cgpa": 8.0})
    assert r.status_code == 200
    run = client.post("/api/run").json()
    assert next(c for c in run["candidates"] if c["name"] == "Karan Singh")["eligibility"]["eligible"]


def test_frontend_is_served_and_path_traversal_is_blocked(client):
    from backend.main import DIST
    if not (DIST / "index.html").exists():
        pytest.skip("frontend not built")
    assert "<div id=\"root\">" in client.get("/results").text          # SPA fallback for deep links
    assert client.get("/api/nope").status_code == 404                   # unknown API routes are not swallowed
    for evil in ["/../backend/main.py", "/%2e%2e/backend/main.py", "/..%5cbackend%5cmain.py"]:
        body = client.get(evil).text
        assert "FastAPI(" not in body and "init_db" not in body        # never leaks source files


def test_loading_samples_never_overwrites_the_users_job_and_reports_duplicates(client):
    client.put("/api/job", json={"title": "My Own Job", "required_skills": ["Rust"], "min_cgpa": 9})
    first = client.post("/api/samples/load").json()
    assert first["added"] == 10 and first["sample_job_applied"] is False  # 7 PDFs + 3 DOCX variants
    assert client.get("/api/job").json()["title"] == "My Own Job"            # untouched
    second = client.post("/api/samples/load").json()
    assert second["added"] == 0 and second["already_loaded"] == 10            # all 10 already present


def test_loading_samples_for_a_new_user_applies_the_sample_job(client):
    body = client.post("/api/samples/load").json()
    assert body["sample_job_applied"] is True and client.get("/api/job").json()["location"] == "Bengaluru"
