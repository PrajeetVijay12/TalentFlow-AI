"""Safe handling of uploaded resume files.

Security measures:
  * only .pdf / .docx accepted, and the file's first bytes must match the type
  * size limit (5 MB)
  * the original filename is sanitized and NEVER used as a storage path
  * files are saved under random names in backend/uploads (not served publicly)
  * resume text is never written to the logs
"""
from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path

from backend.models.schemas import CandidateProfile
from backend.parsing.resume_parser import parse_resume_text
from backend.parsing.text_extractor import ParseError, extract_text
from backend.services import database as db

MAX_BYTES = 5 * 1024 * 1024
ALLOWED = {"pdf": b"%PDF", "docx": b"PK\x03\x04"}
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data" / "resumes"


def sanitize_filename(name: str) -> str:
    name = Path(name or "").name                       # drop any directory part
    name = re.sub(r"[^A-Za-z0-9._\- ]", "_", name).strip(" .")
    return name[:100] or "resume"


def process_upload(uid: int, filename: str, data: bytes) -> dict:
    """Validate, parse and store ONE uploaded file for user `uid`. Never raises; returns a status dict."""
    safe = sanitize_filename(filename)
    ext = safe.rsplit(".", 1)[-1].lower() if "." in safe else ""
    if ext not in ALLOWED:
        return {"filename": safe, "status": "error", "message": "Unsupported file type. Please upload a PDF or DOCX resume."}
    if len(data) == 0:
        return {"filename": safe, "status": "error", "message": "The file is empty."}
    if len(data) > MAX_BYTES:
        return {"filename": safe, "status": "error", "message": f"File is larger than {MAX_BYTES // (1024 * 1024)} MB."}
    if not data.startswith(ALLOWED[ext]):
        return {"filename": safe, "status": "error", "message": f"The file content is not a valid {ext.upper()} document."}

    sha = hashlib.sha256(data).hexdigest()
    existing = db.find_by_hash(uid, sha)
    if existing:
        return {"filename": safe, "status": "duplicate", "message": f"Duplicate of an already uploaded resume ({existing.name}).",
                "candidate": existing.model_dump()}
    try:
        text = extract_text(safe, data)
    except ParseError as e:
        return {"filename": safe, "status": "error", "message": str(e)}

    cand = parse_resume_text(text, safe)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / f"{uuid.uuid4().hex}.{ext}").write_bytes(data)
    cand = db.add_candidate(uid, sha, cand)
    msg = "Parsed successfully." if not cand.missing_fields else "Parsed. Missing: " + ", ".join(cand.missing_fields) + "."
    return {"filename": safe, "status": "ok", "message": msg, "candidate": cand.model_dump()}
