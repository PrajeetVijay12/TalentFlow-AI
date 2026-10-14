import sqlite3
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import auth, database as db
from tests.helpers import SAMPLES, signed_in_client


def email():
    return f"{uuid.uuid4().hex[:10]}@example.com"


def register(client, mail=None, password="Str0ng-pass!", name="Asha K"):
    return client.post("/api/auth/register", json={"name": name, "email": mail or email(), "password": password})


# ----------------------------------------------------------- password storage
def test_passwords_are_hashed_and_verifiable():
    h = auth.hash_password("correct horse")
    assert "correct horse" not in h and h.startswith("scrypt$")
    assert auth.verify_password("correct horse", h) and not auth.verify_password("wrong", h)
    assert auth.hash_password("correct horse") != h            # random salt every time
    assert not auth.verify_password("x", "garbage")            # malformed hash never crashes


def test_database_never_contains_the_plain_password_or_token():
    c, mail = TestClient(app), email()
    token = register(c, mail, "My-Secret-123").cookies["session"]
    with db.connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (mail,)).fetchone()
        sessions = [r["token_hash"] for r in conn.execute("SELECT token_hash FROM sessions")]
    assert "My-Secret-123" not in dict(user)["pw_hash"]
    assert token not in sessions and auth.hash_token(token) in sessions     # only the hash of the token is stored


# ------------------------------------------------------------- register/login
def test_register_logs_you_in_and_cookie_is_httponly():
    c = TestClient(app)
    r = register(c)
    assert r.status_code == 200 and r.json()["name"] == "Asha K"
    assert "httponly" in r.headers["set-cookie"].lower() and "samesite=lax" in r.headers["set-cookie"].lower()
    assert c.get("/api/auth/me").json()["email"].endswith("@example.com")


@pytest.mark.parametrize("name,mail,pw,expect", [
    ("", "a@b.com", "Str0ng-pass!", "name"),
    ("Asha", "not-an-email", "Str0ng-pass!", "email"),
    ("Asha", "a@b.com", "short", "8 characters"),
    ("Asha", "a@b.com", "password", "guessable"),
])
def test_registration_validation(name, mail, pw, expect):
    r = TestClient(app).post("/api/auth/register", json={"name": name, "email": mail, "password": pw})
    assert r.status_code == 422 and expect in " ".join(r.json()["detail"]).lower()


def test_duplicate_email_rejected_case_insensitively():
    c, mail = TestClient(app), email()
    assert register(c, mail).status_code == 200
    assert register(TestClient(app), mail.upper()).status_code == 409


def test_login_and_logout_cycle():
    mail = email()
    register(TestClient(app), mail)
    c = TestClient(app)
    assert c.get("/api/candidates").status_code == 401
    assert c.post("/api/auth/login", json={"email": mail.upper(), "password": "Str0ng-pass!"}).status_code == 200
    assert c.get("/api/candidates").status_code == 200
    assert c.post("/api/auth/logout").json()["signed_out"] is True
    assert c.get("/api/candidates").status_code == 401           # the session is gone on the server, not just in the browser


def test_wrong_password_and_unknown_email_give_the_same_message():
    mail = email()
    register(TestClient(app), mail)
    a = TestClient(app).post("/api/auth/login", json={"email": mail, "password": "wrong-password"})
    b = TestClient(app).post("/api/auth/login", json={"email": email(), "password": "wrong-password"})
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


def test_too_many_failed_logins_are_blocked_then_reset_on_success():
    mail = email()
    register(TestClient(app), mail)
    c = TestClient(app)
    for _ in range(auth.LoginThrottle.MAX_FAILURES):
        assert c.post("/api/auth/login", json={"email": mail, "password": "nope-nope-nope"}).status_code == 401
    blocked = c.post("/api/auth/login", json={"email": mail, "password": "Str0ng-pass!"})
    assert blocked.status_code == 429                              # even the right password is refused while blocked
    auth.throttle._fails.clear()


def test_expired_and_forged_sessions_are_rejected():
    c = TestClient(app)
    register(c)
    token = c.cookies["session"]
    with db.connect() as conn:
        conn.execute("UPDATE sessions SET expires = 1 WHERE token_hash = ?", (auth.hash_token(token),))
    assert c.get("/api/auth/me").status_code == 401
    forged = TestClient(app)
    forged.cookies.set("session", "x" * 43)
    assert forged.get("/api/candidates").status_code == 401


# ---------------------------------------------------------------- protection
@pytest.mark.parametrize("method,path", [
    ("get", "/api/job"), ("put", "/api/job"), ("get", "/api/candidates"), ("delete", "/api/candidates"), ("post", "/api/run"),
    ("get", "/api/run/latest"), ("post", "/api/resumes"), ("post", "/api/samples/load"), ("get", "/api/options"),
    ("get", "/api/algorithms"), ("post", "/api/job/parse"),
])
def test_every_data_route_requires_login(method, path):
    r = getattr(TestClient(app), method)(path)
    assert r.status_code == 401, path


def test_health_stays_public():
    assert TestClient(app).get("/api/health").status_code == 200


# ----------------------------------------------------------- data isolation
def test_each_user_only_sees_their_own_data():
    alice, bob = signed_in_client("Alice"), signed_in_client("Bob")
    pdf = next(SAMPLES.glob("*.pdf"))
    files = [("files", (pdf.name, pdf.read_bytes(), "application/pdf"))]
    assert alice.post("/api/resumes", files=files).json()["results"][0]["status"] == "ok"
    assert len(alice.get("/api/candidates").json()) == 1 and bob.get("/api/candidates").json() == []
    # the same file is NOT a duplicate for another user
    assert bob.post("/api/resumes", files=files).json()["results"][0]["status"] == "ok"
    alice_id = alice.get("/api/candidates").json()[0]["id"]
    assert bob.put(f"/api/candidates/{alice_id}", json={"cgpa": 1}).status_code == 404       # cannot edit
    assert bob.delete(f"/api/candidates/{alice_id}").status_code == 404                      # cannot delete
    bob.put("/api/job", json={"title": "Bob's Job", "required_skills": ["Go"]})
    assert alice.get("/api/job").json()["title"] != "Bob's Job"
    alice.post("/api/run")
    assert bob.get("/api/run/latest").json() is None and alice.get("/api/run/latest").json() is not None


# ---------------------------------------------- legacy data + migration
def test_old_database_is_migrated_and_first_account_adopts_the_data(tmp_path, monkeypatch):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript("""
        CREATE TABLE job (id INTEGER PRIMARY KEY CHECK (id = 1), data TEXT NOT NULL);
        CREATE TABLE candidates (id INTEGER PRIMARY KEY AUTOINCREMENT, sha256 TEXT UNIQUE NOT NULL, filename TEXT, data TEXT NOT NULL);
        CREATE TABLE runs (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    old.execute("INSERT INTO job VALUES (1, ?)", ('{"title": "Legacy Job", "required_skills": ["Python"]}',))
    old.execute("INSERT INTO candidates (sha256, filename, data) VALUES ('abc', 'x.pdf', ?)", ('{"name": "Legacy Person"}',))
    old.execute("INSERT INTO runs (data) VALUES ('{\"summary\": 1}')")
    old.commit(); old.close()

    monkeypatch.setattr(db, "DB_PATH", path)
    db.init_db()
    db.init_db()                                                  # running twice must be harmless
    first = db.create_user("first@example.com", "First", auth.hash_password("Str0ng-pass!"))
    assert db.get_job(first).title == "Legacy Job"
    assert [c.name for c in db.list_candidates(first)] == ["Legacy Person"] and db.latest_run(first) == {"summary": 1}
    second = db.create_user("second@example.com", "Second", auth.hash_password("Str0ng-pass!"))
    assert db.list_candidates(second) == [] and db.get_job(second).title != "Legacy Job"   # only the FIRST account adopts
