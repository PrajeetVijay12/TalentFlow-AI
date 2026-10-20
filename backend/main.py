"""FastAPI entry point.   Run from the project root:   uvicorn backend.main:app --reload

If the frontend has been built (cd frontend && npm run build), this same server also
serves the web app, so ONE command runs the whole project at http://127.0.0.1:8000
"""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.api.auth_routes import router as auth_router
from backend.api.routes import public, router
from backend.api.testcase_routes import router as tc_router
from backend.services.database import init_db

DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

app = FastAPI(title="TalentFlow AI — Intelligent Recruitment Platform")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()
app.include_router(auth_router)
app.include_router(public)
app.include_router(router)
app.include_router(tc_router)


if (DIST / "index.html").exists():

    @app.get("/{path:path}", include_in_schema=False)
    def serve_frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, detail="Not found.")
        target = (DIST / path).resolve()
        # only serve real files that live inside the dist folder (blocks ../ tricks)
        if path and DIST.resolve() in target.parents and target.is_file():
            return FileResponse(target)
        return FileResponse(DIST / "index.html")  # single-page-app fallback for /results, /candidates/3 ...
