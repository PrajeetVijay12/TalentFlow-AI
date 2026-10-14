"""Tiny SQLite storage (Python standard library only).

Every recruiter has their own account; the job, candidates and runs are stored per user_id.
Rows created before accounts existed live under user_id = 0 and are adopted by the first
account that registers (see create_user).
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from backend.models.schemas import CandidateProfile, JobRequirements

BASE = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("RESUME_DB", BASE / "data" / "app.db"))


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _columns(c: sqlite3.Connection, table: str) -> list[str]:
    return [r["name"] for r in c.execute(f"PRAGMA table_info({table})")]


def _migrate_to_per_user(c: sqlite3.Connection) -> None:
    """Upgrade a database created before accounts existed: old rows move to user_id = 0."""
    cols = _columns(c, "job")
    if cols and "user_id" not in cols:
        c.execute("ALTER TABLE job RENAME TO job_old")
        c.execute("CREATE TABLE job (user_id INTEGER PRIMARY KEY, data TEXT NOT NULL)")
        c.execute("INSERT INTO job (user_id, data) SELECT 0, data FROM job_old")
        c.execute("DROP TABLE job_old")
    cols = _columns(c, "candidates")
    if cols and "user_id" not in cols:
        c.execute("ALTER TABLE candidates RENAME TO candidates_old")
        c.execute("""CREATE TABLE candidates (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL DEFAULT 0,
                     sha256 TEXT NOT NULL, filename TEXT, data TEXT NOT NULL, UNIQUE (user_id, sha256))""")
        c.execute("INSERT INTO candidates (id, user_id, sha256, filename, data) SELECT id, 0, sha256, filename, data FROM candidates_old")
        c.execute("DROP TABLE candidates_old")
    cols = _columns(c, "runs")
    if cols and "user_id" not in cols:
        c.execute("ALTER TABLE runs ADD COLUMN user_id INTEGER NOT NULL DEFAULT 0")


def init_db() -> None:
    with connect() as c:
        _migrate_to_per_user(c)
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                pw_hash TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS job (user_id INTEGER PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL DEFAULT 0,
                sha256 TEXT NOT NULL, filename TEXT, data TEXT NOT NULL, UNIQUE (user_id, sha256));
            CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL DEFAULT 0,
                data TEXT NOT NULL, created TEXT DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS recruitments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
                name TEXT NOT NULL DEFAULT 'Recruitment',
                job_data TEXT NOT NULL, run_data TEXT,
                candidates_count INTEGER DEFAULT 0,
                created TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'complete');
        """)


# ----------------------------------------------------------------- users
def create_user(email: str, name: str, pw_hash: str) -> int:
    """Insert a user. The very first account adopts the pre-accounts data (user_id 0)."""
    with connect() as c:
        cur = c.execute("INSERT INTO users (email, name, pw_hash) VALUES (?, ?, ?)", (email, name, pw_hash))
        uid = cur.lastrowid
        if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1:
            for table in ("job", "candidates", "runs"):
                c.execute(f"UPDATE {table} SET user_id = ? WHERE user_id = 0", (uid,))
        return uid


def user_by_email(email: str) -> Optional[dict]:
    with connect() as c:
        row = c.execute("SELECT id, email, name, pw_hash FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def create_session(uid: int, token_hash: str, expires: float) -> None:
    with connect() as c:
        c.execute("DELETE FROM sessions WHERE expires < ?", (time.time(),))  # tidy up expired sessions
        c.execute("INSERT INTO sessions (token_hash, user_id, expires) VALUES (?, ?, ?)", (token_hash, uid, expires))


def user_by_session(token_hash: str) -> Optional[dict]:
    with connect() as c:
        row = c.execute("""SELECT u.id, u.email, u.name FROM sessions s JOIN users u ON u.id = s.user_id
                           WHERE s.token_hash = ? AND s.expires > ?""", (token_hash, time.time())).fetchone()
    return dict(row) if row else None


def delete_session(token_hash: str) -> None:
    with connect() as c:
        c.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))


# ------------------------------------------------------------------- job
def get_job(uid: int) -> JobRequirements:
    with connect() as c:
        row = c.execute("SELECT data FROM job WHERE user_id = ?", (uid,)).fetchone()
    return JobRequirements(**json.loads(row["data"])) if row else JobRequirements()


def has_job(uid: int) -> bool:
    with connect() as c:
        return c.execute("SELECT 1 FROM job WHERE user_id = ?", (uid,)).fetchone() is not None


def save_job(uid: int, job: JobRequirements) -> None:
    with connect() as c:
        c.execute("INSERT OR REPLACE INTO job (user_id, data) VALUES (?, ?)", (uid, job.model_dump_json()))


# ------------------------------------------------------------ candidates
def find_by_hash(uid: int, sha: str) -> Optional[CandidateProfile]:
    with connect() as c:
        row = c.execute("SELECT id, data FROM candidates WHERE user_id = ? AND sha256 = ?", (uid, sha)).fetchone()
    return _to_candidate(row) if row else None


def add_candidate(uid: int, sha: str, cand: CandidateProfile) -> CandidateProfile:
    with connect() as c:
        cur = c.execute("INSERT INTO candidates (user_id, sha256, filename, data) VALUES (?, ?, ?, ?)",
                        (uid, sha, cand.filename, cand.model_dump_json()))
        cand.id = cur.lastrowid
        c.execute("UPDATE candidates SET data = ? WHERE id = ?", (cand.model_dump_json(), cand.id))
    return cand


def update_candidate(uid: int, cand: CandidateProfile) -> None:
    with connect() as c:
        c.execute("UPDATE candidates SET data = ? WHERE id = ? AND user_id = ?", (cand.model_dump_json(), cand.id, uid))


def list_candidates(uid: int) -> list[CandidateProfile]:
    with connect() as c:
        rows = c.execute("SELECT id, data FROM candidates WHERE user_id = ? ORDER BY id", (uid,)).fetchall()
    return [_to_candidate(r) for r in rows]


def get_candidate(uid: int, cid: int) -> Optional[CandidateProfile]:
    with connect() as c:
        row = c.execute("SELECT id, data FROM candidates WHERE id = ? AND user_id = ?", (cid, uid)).fetchone()
    return _to_candidate(row) if row else None


def delete_candidate(uid: int, cid: int) -> bool:
    with connect() as c:
        return c.execute("DELETE FROM candidates WHERE id = ? AND user_id = ?", (cid, uid)).rowcount > 0


def clear_candidates(uid: int) -> None:
    with connect() as c:
        c.execute("DELETE FROM candidates WHERE user_id = ?", (uid,))
        c.execute("DELETE FROM runs WHERE user_id = ?", (uid,))


def _to_candidate(row) -> CandidateProfile:
    cand = CandidateProfile(**json.loads(row["data"]))
    cand.id = row["id"]
    return cand


# ------------------------------------------------------------------ runs
def save_run(uid: int, result: dict) -> None:
    with connect() as c:
        c.execute("INSERT INTO runs (user_id, data) VALUES (?, ?)", (uid, json.dumps(result)))
        c.execute("DELETE FROM runs WHERE user_id = ? AND id NOT IN (SELECT id FROM runs WHERE user_id = ? ORDER BY id DESC LIMIT 5)",
                  (uid, uid))


def latest_run(uid: int) -> Optional[dict]:
    with connect() as c:
        row = c.execute("SELECT data FROM runs WHERE user_id = ? ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    return json.loads(row["data"]) if row else None


# --------------------------------------------------------- recruitments
def save_recruitment(uid: int, job: JobRequirements, run_data: dict, candidates_count: int) -> int:
    import datetime
    name = f"{job.title} — {datetime.datetime.now().strftime('%b %d, %Y')}"
    with connect() as c:
        cur = c.execute(
            "INSERT INTO recruitments (user_id, name, job_data, run_data, candidates_count, status) VALUES (?,?,?,?,?,?)",
            (uid, name, job.model_dump_json(), json.dumps(run_data), candidates_count, "complete"),
        )
        return cur.lastrowid


def list_recruitments(uid: int) -> list[dict]:
    with connect() as c:
        rows = c.execute(
            "SELECT id, name, job_data, candidates_count, created, status FROM recruitments WHERE user_id = ? ORDER BY id DESC",
            (uid,),
        ).fetchall()
    result = []
    for r in rows:
        job = json.loads(r["job_data"])
        result.append({
            "id": r["id"], "name": r["name"], "created": r["created"],
            "status": r["status"], "candidates_count": r["candidates_count"],
            "title": job.get("title", ""), "location": job.get("location"),
            "openings": job.get("openings", 1),
        })
    return result


def get_recruitment(uid: int, rid: int) -> Optional[dict]:
    with connect() as c:
        row = c.execute(
            "SELECT id, name, job_data, run_data, candidates_count, created, status FROM recruitments WHERE id = ? AND user_id = ?",
            (rid, uid),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"], "name": row["name"], "created": row["created"],
        "status": row["status"], "candidates_count": row["candidates_count"],
        "job": json.loads(row["job_data"]),
        "run": json.loads(row["run_data"]) if row["run_data"] else None,
    }


def delete_recruitment(uid: int, rid: int) -> bool:
    with connect() as c:
        return c.execute("DELETE FROM recruitments WHERE id = ? AND user_id = ?", (rid, uid)).rowcount > 0
