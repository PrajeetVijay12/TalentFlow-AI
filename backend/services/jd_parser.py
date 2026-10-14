"""Reads a pasted job description and suggests values for the criteria form.

Deterministic keyword / regex matching only (same dictionaries as the resume parser).
It only SUGGESTS values: the recruiter reviews them in the dropdowns before saving.
"""
from __future__ import annotations

import re

from backend.parsing.normalizer import (
    JOB_TITLES, find_all_degrees, find_certs_in_text, find_location_in_text, find_skills_in_text,
)


def _experience(text: str) -> float | None:
    if re.search(r"\bfreshers?\b|no experience (?:is )?(?:required|needed)|entry[- ]level", text, re.IGNORECASE):
        return 0.0
    for sentence in re.split(r"[.\n;]", text):
        if "experience" not in sentence.lower():
            continue
        m = re.search(r"(\d+(?:\.\d+)?)\s*(?:\+|plus)?\s*(?:(?:-|to)\s*\d+\s*)?(years?|yrs?|months?)", sentence, re.IGNORECASE)
        if m:
            v = float(m.group(1))
            return round(v / 12, 2) if m.group(2).lower().startswith("month") else v
    return None


def _cgpa(text: str) -> float | None:
    for pat in (r"(?:cgpa|gpa)\s*(?:of|>=|≥|:|-|above|minimum)?\s*(\d{1,2}(?:\.\d{1,2})?)",
                r"(\d{1,2}(?:\.\d{1,2})?)\s*\+?\s*(?:cgpa|gpa)"):
        m = re.search(pat, text, re.IGNORECASE)
        if m and 0 < float(m.group(1)) <= 10:
            return float(m.group(1))
    if re.search(r"aggregate|percentage|marks", text, re.IGNORECASE):
        m = re.search(r"(\d{2,3})\s*%", text)
        if m and 40 <= float(m.group(1)) <= 100:
            return round(float(m.group(1)) / 10, 1)
    return None


def parse_job_description(text: str) -> dict:
    text = text or ""
    suggestion: dict = {}
    found: list[str] = []

    first = next((ln.strip() for ln in text.split("\n") if ln.strip()), "")
    title = next((t for t in JOB_TITLES if t.lower() in text.lower()), None)
    if not title and 3 <= len(first) <= 60 and len(first.split()) <= 6:
        title = first
    if title:
        suggestion["title"] = title
        found.append("job title")

    degrees = find_all_degrees(text)
    if degrees:
        suggestion["required_degrees"] = degrees
        found.append("degrees")
    cg = _cgpa(text)
    if cg is not None:
        suggestion["min_cgpa"] = cg
        found.append("minimum CGPA")
    exp = _experience(text)
    if exp is not None:
        suggestion["min_experience"] = exp
        found.append("experience")
    skills = find_skills_in_text(text)
    if skills:
        suggestion["required_skills"] = skills
        found.append("skills")
    certs = find_certs_in_text(text)
    if certs:
        suggestion["required_certifications"] = certs
        found.append("certifications")
        if re.search(r"certif\w*\s+(?:is\s+)?(?:mandatory|required|must)|must\s+(?:have|hold)\s+\w*\s*certif", text, re.IGNORECASE):
            suggestion["certifications_mandatory"] = True
    loc = find_location_in_text(text)
    if loc:
        suggestion["location"] = loc
        found.append("location")
    m = re.search(r"(\d+)\s*(?:openings?|positions?|vacancies|hires?)", text, re.IGNORECASE)
    if m and 1 <= int(m.group(1)) <= 100:
        suggestion["openings"] = int(m.group(1))
        found.append("openings")

    all_fields = ["job title", "degrees", "minimum CGPA", "experience", "skills", "certifications", "location", "openings"]
    return {"suggestion": suggestion, "found": found, "not_found": [f for f in all_fields if f not in found]}
