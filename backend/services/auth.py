"""Password hashing, session tokens and login throttling (standard library only).

* Passwords are never stored: only a salted scrypt hash.
* A session token is 32 random bytes; the database stores only its SHA-256, so a leaked
  database cannot be used to log in.
* Too many failed logins for the same email/IP are temporarily blocked.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import time

SESSION_SECONDS = 7 * 24 * 3600
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(digest, bytes.fromhex(digest_hex))
    except (ValueError, TypeError):
        return False


# Verified against when the email is unknown, so "no such user" takes as long as "wrong password".
DUMMY_HASH = hash_password("not-a-real-password")


def new_token() -> tuple[str, str]:
    """Returns (token for the cookie, hash of the token for the database)."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def validate_registration(name: str, email: str, password: str) -> list[str]:
    problems = []
    if not 1 <= len(name.strip()) <= 80:
        problems.append("Enter your name (up to 80 characters).")
    if not EMAIL_RE.match(email) or len(email) > 200:
        problems.append("Enter a valid email address.")
    if len(password) < 8:
        problems.append("Password must be at least 8 characters.")
    elif len(password) > 200:
        problems.append("Password is too long (200 characters maximum).")
    elif password.lower() in {"password", "12345678", "qwertyui", "password1"} or password.lower() == email.split("@")[0].lower():
        problems.append("Choose a less guessable password.")
    return problems


class LoginThrottle:
    """Allow MAX_FAILURES failed logins per key within WINDOW seconds."""
    MAX_FAILURES = 5
    WINDOW = 600

    def __init__(self):
        self._fails: dict[str, list[float]] = {}

    def _recent(self, key: str) -> list[float]:
        now = time.time()
        recent = [t for t in self._fails.get(key, []) if now - t < self.WINDOW]
        self._fails[key] = recent
        return recent

    def blocked(self, key: str) -> bool:
        return len(self._recent(key)) >= self.MAX_FAILURES

    def fail(self, key: str) -> None:
        self._recent(key).append(time.time())

    def reset(self, key: str) -> None:
        self._fails.pop(key, None)


throttle = LoginThrottle()
