"""REST API consumed by the React frontend.

Every route here requires a signed-in user (see auth_routes.current_user) and only ever
touches that user's own job, candidates and results.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import ValidationError

from backend.api.auth_routes import current_user
from backend.models.schemas import CandidateProfile, JobRequirements
from backend.parsing.normalizer import JOB_TITLES, KNOWN_LOCATIONS, known_certs, known_degrees, known_skills
from backend.services import database as db
from backend.services.algorithm_info import ALGORITHM_TABLE, EXPLANATIONS
from backend.services import chatbot
from backend.services.jd_parser import parse_job_description
from backend.services.pipeline import run_pipeline
from backend.services.upload_service import MAX_BYTES, SAMPLE_DIR, process_upload

router = APIRouter(prefix="/api", dependencies=[Depends(current_user)])
public = APIRouter(prefix="/api")


def _pretty_errors(e: ValidationError) -> list[str]:
    out = []
    for err in e.errors():
        field = ".".join(str(p) for p in err["loc"] if p != "body")
        msg = err["msg"].replace("Value error, ", "")
        out.append(f"{field}: {msg}" if field else msg)
    return out


@public.get("/health")
def health():
    return {"status": "ok"}


# ------------------------------------------------------------------ job
@router.get("/job")
def get_job(user: dict = Depends(current_user)):
    return db.get_job(user["id"]).model_dump()


@router.put("/job")
def put_job(payload: dict, user: dict = Depends(current_user)):
    try:
        job = JobRequirements(**payload)
    except ValidationError as e:
        raise HTTPException(422, detail=_pretty_errors(e))
    db.save_job(user["id"], job)
    return job.model_dump()


@router.get("/options")
def options():
    """Values for the dropdowns on the Job Requirements page."""
    return {"titles": JOB_TITLES, "degrees": known_degrees(), "skills": known_skills(),
            "certifications": known_certs(), "locations": KNOWN_LOCATIONS}


@router.post("/job/parse")
def parse_jd(payload: dict):
    """Suggest criteria from a pasted job description (keyword matching, no AI model)."""
    text = str(payload.get("text", ""))
    if len(text.strip()) < 15:
        raise HTTPException(422, detail="Paste the job description first (at least a sentence).")
    return parse_job_description(text[:20000])


# ------------------------------------------------------------ candidates
@router.get("/candidates")
def candidates(user: dict = Depends(current_user)):
    return [c.model_dump() for c in db.list_candidates(user["id"])]


@router.post("/resumes")
async def upload_resumes(files: list[UploadFile] = File(default=[]), user: dict = Depends(current_user)):
    if not files:
        raise HTTPException(400, detail="No resumes uploaded. Choose at least one PDF or DOCX file.")
    results = []
    for f in files:
        data = await f.read(MAX_BYTES + 1)
        results.append(process_upload(user["id"], f.filename or "resume", data))
    return {"results": results}


@router.put("/candidates/{cid}")
def edit_candidate(cid: int, payload: dict, user: dict = Depends(current_user)):
    """Let HR correct a parsed field (human review step)."""
    existing = db.get_candidate(user["id"], cid)
    if not existing:
        raise HTTPException(404, detail="Candidate not found.")
    try:
        merged = CandidateProfile(**{**existing.model_dump(), **payload, "id": cid})
    except ValidationError as e:
        raise HTTPException(422, detail=_pretty_errors(e))
    db.update_candidate(user["id"], merged)
    return merged.model_dump()


@router.delete("/candidates/{cid}")
def remove_candidate(cid: int, user: dict = Depends(current_user)):
    if not db.delete_candidate(user["id"], cid):
        raise HTTPException(404, detail="Candidate not found.")
    return {"deleted": cid}


@router.delete("/candidates")
def remove_all(user: dict = Depends(current_user)):
    db.clear_candidates(user["id"])
    return {"deleted": "all"}


@router.post("/samples/load")
def load_samples(user: dict = Depends(current_user)):
    """Load the bundled sample job and resumes (for demos)."""
    files = sorted(SAMPLE_DIR.glob("*"))
    if not files:
        raise HTTPException(404, detail="Sample resumes not found. Run: python sample_data/generate_samples.py")
    # The samples were written for the sample job (Bengaluru). Use it only if this user has not saved a job yet —
    # never overwrite requirements the user already chose.
    job_set = not db.has_job(user["id"])
    if job_set:
        db.save_job(user["id"], JobRequirements(location="Bengaluru"))
    results = [process_upload(user["id"], p.name, p.read_bytes()) for p in files if p.suffix.lower() in (".pdf", ".docx")]
    added = sum(1 for r in results if r["status"] == "ok")
    return {"results": results, "added": added, "already_loaded": sum(1 for r in results if r["status"] == "duplicate"),
            "sample_job_applied": job_set}


# ------------------------------------------------------------- pipeline
@router.post("/run")
def run(user: dict = Depends(current_user)):
    cands = db.list_candidates(user["id"])
    if not cands:
        raise HTTPException(400, detail="No resumes uploaded. Upload at least one resume before running the pipeline.")
    job = db.get_job(user["id"])
    try:
        result = run_pipeline(job, cands)
    except ValidationError as e:
        raise HTTPException(422, detail=_pretty_errors(e))
    db.save_run(user["id"], result)
    db.save_recruitment(user["id"], job, result, len(cands))
    return result


@router.get("/run/latest")
def latest(user: dict = Depends(current_user)):
    return db.latest_run(user["id"])


@router.get("/algorithms")
def algorithms():
    return {"table": ALGORITHM_TABLE, "explanations": EXPLANATIONS}


# ---------------------------------------------------------- chatbot
@router.post("/chat")
def chat(payload: dict, user: dict = Depends(current_user)):
    """Knowledge-Based HR Query Agent — Unit I (Agents) + Unit IV (Logical Reasoning)."""
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(400, detail="Empty message.")
    run = db.latest_run(user["id"])
    if not run:
        return {"reply": (
            "No screening results yet. Please:\n"
            "1. Set up a job (New Recruitment)\n"
            "2. Upload resumes\n"
            "3. Run the AI pipeline\n"
            "Then come back and ask me anything about the candidates!"
        )}
    job = db.get_job(user["id"])
    reply = chatbot.respond(message, run, job.model_dump())
    return {"reply": reply}


# ------------------------------------------------------------ history
@router.get("/history")
def list_history(user: dict = Depends(current_user)):
    return db.list_recruitments(user["id"])


@router.get("/history/{rid}")
def get_history(rid: int, user: dict = Depends(current_user)):
    item = db.get_recruitment(user["id"], rid)
    if not item:
        raise HTTPException(404, detail="Recruitment not found.")
    return item


@router.delete("/history/{rid}")
def delete_history(rid: int, user: dict = Depends(current_user)):
    if not db.delete_recruitment(user["id"], rid):
        raise HTTPException(404, detail="Recruitment not found.")
    return {"deleted": rid}


@router.post("/history/{rid}/reopen")
def reopen_history(rid: int, user: dict = Depends(current_user)):
    """Load a past recruitment's job requirements as the active job."""
    item = db.get_recruitment(user["id"], rid)
    if not item:
        raise HTTPException(404, detail="Recruitment not found.")
    try:
        job = JobRequirements(**item["job"])
    except ValidationError as e:
        raise HTTPException(422, detail=_pretty_errors(e))
    db.save_job(user["id"], job)
    db.clear_candidates(user["id"])
    return job.model_dump()
