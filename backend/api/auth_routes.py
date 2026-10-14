"""Sign up / log in / log out, and the dependency that protects every other API route."""
from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from backend.services import auth, database as db

COOKIE = "session"
router = APIRouter(prefix="/api/auth")


def current_user(request: Request) -> dict:
    """FastAPI dependency: the signed-in user, or a 401 'please sign in' error."""
    token = request.cookies.get(COOKIE)
    user = db.user_by_session(auth.hash_token(token)) if token else None
    if not user:
        raise HTTPException(401, detail="Please sign in to continue.")
    return user


def _start_session(response: Response, uid: int) -> None:
    token, token_hash = auth.new_token()
    db.create_session(uid, token_hash, time.time() + auth.SESSION_SECONDS)
    # HttpOnly: JavaScript cannot read the cookie. SameSite=Lax: other websites cannot make the browser send it on POSTs.
    response.set_cookie(COOKIE, token, max_age=auth.SESSION_SECONDS, httponly=True, samesite="lax", path="/")


def _public(user: dict) -> dict:
    return {"id": user["id"], "name": user["name"], "email": user["email"]}


@router.post("/register")
def register(payload: dict, response: Response):
    name, email = str(payload.get("name", "")).strip(), str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    problems = auth.validate_registration(name, email, password)
    if problems:
        raise HTTPException(422, detail=problems)
    if db.user_by_email(email):
        raise HTTPException(409, detail="An account with this email already exists. Try signing in.")
    uid = db.create_user(email, name, auth.hash_password(password))
    _start_session(response, uid)
    return _public({"id": uid, "name": name, "email": email})


@router.post("/login")
def login(payload: dict, request: Request, response: Response):
    email, password = str(payload.get("email", "")).strip().lower(), str(payload.get("password", ""))
    key = f"{email}|{request.client.host if request.client else '?'}"
    if auth.throttle.blocked(key):
        raise HTTPException(429, detail="Too many failed attempts. Please wait a few minutes and try again.")
    user = db.user_by_email(email)
    ok = auth.verify_password(password, user["pw_hash"] if user else auth.DUMMY_HASH)
    if not (user and ok):
        auth.throttle.fail(key)
        raise HTTPException(401, detail="Incorrect email or password.")  # same message for both cases
    auth.throttle.reset(key)
    _start_session(response, user["id"])
    return _public(user)


@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(COOKIE)
    if token:
        db.delete_session(auth.hash_token(token))
    response.delete_cookie(COOKIE, path="/")
    return {"signed_out": True}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return _public(user)
