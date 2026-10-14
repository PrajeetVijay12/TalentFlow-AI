"""Rule-based resume parser (information extraction).

Pipeline:  raw text -> lines -> sections -> field extractors -> CandidateProfile

Every extractor uses regular expressions / dictionaries only, so the result is
deterministic, and each one writes a short note saying HOW the value was found.
"""
from __future__ import annotations

import re
from datetime import date

from backend.models.schemas import PROJECT_SCORES, CandidateProfile, Project
from backend.parsing.normalizer import (
    canonical_cert, canonical_skill, cert_key, dedupe, find_degree, find_skills_in_text, skill_key,
)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{3,5}\)?[\s\-]?)?\d{3,5}[\s\-]?\d{4,5}(?!\d)")

SECTION_ALIASES = {
    "education": {"education", "academic qualifications", "academics", "educational qualifications", "qualifications"},
    "skills": {"skills", "technical skills", "key skills", "core competencies", "skills & tools", "skills and tools",
               "technical proficiency", "technologies"},
    "experience": {"experience", "work experience", "professional experience", "employment", "employment history",
                   "work history", "internships", "internship experience"},
    "projects": {"projects", "academic projects", "personal projects", "key projects", "project experience"},
    "certifications": {"certifications", "certificates", "licenses", "licenses & certifications",
                       "certifications & courses", "courses & certifications"},
    "summary": {"summary", "objective", "career objective", "profile", "professional summary", "about me"},
}
_HEADING_LOOKUP = {alias: sec for sec, aliases in SECTION_ALIASES.items() for alias in aliases}

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
_BULLET = "•●▪◦-*–—·"


# -------------------------------------------------------------- sections
def _clean_lines(text: str) -> list[str]:
    text = text.replace("\r", "\n").replace("\u00a0", " ")
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text)  # PDF bullets often extract as control characters
    return [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.split("\n")]


def _heading_of(line: str) -> str | None:
    key = line.strip(" :-–—_*#|").lower()
    return _HEADING_LOOKUP.get(key)


def split_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"header": []}
    current = "header"
    for ln in lines:
        if not ln:
            continue
        sec = _heading_of(ln)
        if sec:
            current = sec
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(ln)
    return sections


def _strip_bullet(line: str) -> str:
    return line.lstrip(_BULLET + " \t").strip()


# ----------------------------------------------------------------- fields
def _extract_name(lines: list[str], header: list[str], notes: list[str]) -> str | None:
    for ln in lines[:30]:
        m = re.match(r"^(?:full\s+)?name\s*[:\-]\s*(.+)$", ln, re.IGNORECASE)
        if m:
            notes.append("Name read from a 'Name:' label.")
            return m.group(1).strip()
    for ln in (header or lines[:6]):
        if EMAIL_RE.search(ln) or re.search(r"https?://|www\.|linkedin|github", ln, re.IGNORECASE):
            continue
        if re.search(r"\d", ln) or ":" in ln:
            continue
        low = ln.lower()
        if "resume" in low or "curriculum" in low or "vitae" in low:
            continue
        words = ln.split()
        if 1 <= len(words) <= 5 and all(re.match(r"^[A-Za-z.'\-]+$", w) for w in words):
            notes.append("Name taken from the first heading line of the resume.")
            return " ".join(w if not w.isupper() or len(w) <= 2 else w.title() for w in words)
    return None


def _extract_phone(text: str) -> str | None:
    for m in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 10 <= len(digits) <= 13:
            return m.group().strip()
    return None


def _extract_cgpa(text: str, notes: list[str]) -> float | None:
    pats = [
        (r"(?:cgpa|c\.g\.p\.a|gpa)\s*(?:[:\-=]|of|is)?\s*(\d{1,2}(?:\.\d{1,2})?)\s*(?:/\s*(10(?:\.0)?|4(?:\.0)?))?", 1, 2),
        (r"(\d{1,2}(?:\.\d{1,2})?)\s*(?:/\s*(10(?:\.0)?|4(?:\.0)?))?\s*(?:cgpa|gpa)", 1, 2),
    ]
    for pat, g1, g2 in pats:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = float(m.group(g1))
            scale = m.group(g2)
            if scale and scale.startswith("4"):
                val = round(val / 4 * 10, 2)
                notes.append(f"CGPA converted from a 4-point scale ({m.group(g1)}/4).")
            elif val > 10:
                continue
            else:
                notes.append(f"CGPA read from text '{m.group(0).strip()}'.")
            if 0 < val <= 10:
                return val
    m = re.search(r"(?:percentage|aggregate|marks)\s*[:\-]?\s*(\d{2,3}(?:\.\d+)?)\s*%", text, re.IGNORECASE)
    if m and 0 < float(m.group(1)) <= 100:
        notes.append(f"Percentage {m.group(1)}% converted to CGPA by dividing by 10.")
        return round(float(m.group(1)) / 10, 2)
    return None


def _months_between(sm: int, sy: int, em: int, ey: int) -> int:
    return max(0, (ey - sy) * 12 + (em - sm) + 1)


def _extract_experience(text: str, experience_lines: list[str], notes: list[str]) -> float:
    explicit = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*\+?\s*(years?|yrs?|months?)\b(?:\s+of)?\s+(?:[a-z]+\s+){0,2}experience", text, re.IGNORECASE):
        v = float(m.group(1))
        explicit.append(v / 12 if m.group(2).lower().startswith("month") else v)
    for m in re.finditer(r"experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*\+?\s*(years?|yrs?|months?)\b", text, re.IGNORECASE):
        v = float(m.group(1))
        explicit.append(v / 12 if m.group(2).lower().startswith("month") else v)
    if explicit:
        notes.append("Experience read from an explicit statement such as '2 years of experience'.")
        return round(max(explicit), 2)

    # Otherwise add up date ranges inside the Experience section.
    month = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?"
    rng = re.compile(
        rf"(?:{month}\s+)?(\d{{4}})\s*(?:-|–|—|to)\s*(?:{month}\s+)?(\d{{4}}|present|current|till\s+date|now)",
        re.IGNORECASE)
    total = 0
    today = date.today()
    found = 0
    for ln in experience_lines:
        for m in rng.finditer(ln):
            sm = _MONTHS.get((m.group(1) or "jan")[:3].lower(), 1)
            sy = int(m.group(2))
            if m.group(4).isdigit():
                ey, em = int(m.group(4)), _MONTHS.get((m.group(3) or "dec")[:3].lower(), 12)
            else:
                ey, em = today.year, today.month
            total += _months_between(sm, sy, em, ey)
            found += 1
    if found:
        notes.append(f"Experience calculated by adding {found} date range(s) in the Experience section.")
        return round(total / 12, 2)
    return 0.0


_CONTACT_SPLIT = re.compile(r"\s*[|•·●▪]\s*|\s{3,}")


def _location_from_contact_line(lines: list[str]) -> str | None:
    """'Chennai | 9363389320 | name@mail.com' -> 'Chennai'. Looks only at lines that hold contact details."""
    for ln in lines[:40]:
        if not (EMAIL_RE.search(ln) or re.search(r"\d{10}", re.sub(r"[\s\-]", "", ln))):
            continue
        for seg in _CONTACT_SPLIT.split(ln):
            seg = seg.strip(" ,;-")
            if not seg or re.search(r"\d|@|https?:|www\.|linkedin|github|\.com|\.in\b|:", seg, re.IGNORECASE):
                continue
            words = seg.replace(",", " ").split()
            if 1 <= len(words) <= 4 and all(re.match(r"^[A-Za-z.'\-]+$", w) for w in words):
                return seg
    return None


_NOT_A_PROJECT = re.compile(
    r"college|school|university|institute|academy|secondary|higher|diploma|\bb\.?\s?tech|\bb\.?\s?e\b|\bm\.?\s?tech|"
    r"engineering|cgpa|gpa|percentage|\bpresent\b|intern|certif|course|award|winner|prize|place\b|hackathon|"
    r"experience|summary|objective|skills?\b", re.IGNORECASE)


def _orphan_projects(lines: list[str]) -> list[str]:
    """Fallback for scrambled (multi-column) PDFs where the PROJECTS heading is separated from its content.

    Picks lines shaped like 'Project Name – short description': a capitalised name of at most 6 words,
    a dash, then a description. Education, job-role, date, bullet and award lines are filtered out.
    """
    found: list[str] = []
    for ln in lines:
        if not ln or ln[0] in _BULLET or _heading_of(ln):
            continue
        parts = re.split(r"\s+[–—-]\s+", ln, maxsplit=1)
        if len(parts) != 2:
            continue
        name, desc = parts[0].strip(), parts[1].strip()
        words = name.split()
        if not (1 <= len(words) <= 6 and len(desc.split()) >= 2 and name[0].isupper()):
            continue
        if name.isupper() or re.search(r"\d{4}|%|@|\||,", name):  # ALL-CAPS = a job role; digits/commas = dates or places
            continue
        if _NOT_A_PROJECT.search(ln):
            continue
        found.append(ln)
    return found


def _classify_project(line: str) -> tuple[str, str]:
    low = line.lower()
    if re.search(r"\bmini\b", low):
        return "mini", "contains the word 'mini'"
    if re.search(r"college|final[- ]year|capstone|academic|university|semester", low) and "major" in low:
        return "college_major", "college/academic major project"
    if re.search(r"final[- ]year|capstone", low):
        return "college_major", "final-year/capstone project"
    if re.search(r"\bmajor\b", low):
        return "major", "contains the word 'major'"
    return "mini", "no 'major' keyword found, treated as a mini project"


def _extract_projects(lines: list[str]) -> list[Project]:
    projects: list[Project] = []
    for ln in lines:
        text = _strip_bullet(ln)
        if len(text) < 3:
            continue
        name = re.split(r"\s+[-–—]\s+|:\s+|\s*\(|\s*\|\s*", text, maxsplit=1)[0].strip(" .,-") or text
        cat, why = _classify_project(text)
        projects.append(Project(name=name[:100], category=cat, score=PROJECT_SCORES[cat], evidence=why))
    return projects


def _split_items(lines: list[str]) -> list[str]:
    items: list[str] = []
    for ln in lines:
        ln = _strip_bullet(ln)
        if ":" in ln and len(ln.split(":", 1)[0].split()) <= 3:  # "Languages: Python, Java"
            ln = ln.split(":", 1)[1]
        items.extend(p.strip() for p in re.split(r"[,;|•●▪/]|\s{2,}", ln) if p.strip())
    return items


# ------------------------------------------------------------------ main
def parse_resume_text(text: str, filename: str = "") -> CandidateProfile:
    notes: list[str] = []
    lines = _clean_lines(text)
    sections = split_sections(lines)
    full = "\n".join(lines)

    name = _extract_name(lines, sections.get("header", []), notes)
    email_m = EMAIL_RE.search(full)
    email = email_m.group().lower() if email_m else None
    phone = _extract_phone(full.replace(email or "", " "))

    edu_text = "\n".join(sections.get("education", [])) or full
    degree = None
    m = re.search(r"degree\s*[:\-]\s*(.+)", full, re.IGNORECASE)
    if m:
        degree = find_degree(m.group(1))
        if degree:
            notes.append("Degree read from a 'Degree:' label and normalized.")
    if not degree:
        degree = find_degree(edu_text) or find_degree(full)
        if degree:
            notes.append("Degree found by pattern matching in the Education section and normalized.")
    cgpa = _extract_cgpa(edu_text, notes) or _extract_cgpa(full, notes)

    # skills: explicit section + dictionary scan of whole text
    section_skills = [canonical_skill(s) for s in _split_items(sections.get("skills", []))
                      if 0 < len(s) <= 30 and not re.search(r"[.!?]$", s)]
    # Certification lines are excluded from the scan so "AWS Certified ..." is not counted as a skill.
    cert_lines = set(sections.get("certifications", []))
    scanned = find_skills_in_text("\n".join(ln for ln in lines if ln not in cert_lines))
    skills = dedupe(section_skills + scanned, skill_key)
    if skills:
        notes.append(f"{len(skills)} skills found (Skills section + dictionary scan).")

    experience = _extract_experience(full, sections.get("experience", []), notes)
    projects = _extract_projects(sections.get("projects", []))
    if not projects:  # the PROJECTS heading may be separated from its content in a scrambled two-column PDF
        orphans = _orphan_projects(lines)
        if orphans:
            projects = _extract_projects(orphans)
            notes.append(f"No usable Projects section (the PDF layout looks multi-column); {len(projects)} project(s) "
                         "recovered from lines shaped like 'Name – description'. Please check them.")
    certs_raw = _split_items(sections.get("certifications", []))
    for ln in lines:  # lines elsewhere that say "... certified ..." / "certification"
        if re.search(r"\bcertified\b|\bcertification\b", ln, re.IGNORECASE) and ln not in sections.get("certifications", []) \
                and not _heading_of(ln):
            certs_raw.append(ln)
    certifications = dedupe([canonical_cert(c) for c in certs_raw if c.strip()], cert_key)

    loc = None
    m = re.search(r"(?:location|city|address|based in)\s*[:\-]\s*(.+)", full, re.IGNORECASE)
    if m:
        loc = m.group(1).strip().split("|")[0].strip()[:60]
        notes.append("Location read from a 'Location:' label.")
    else:
        loc = _location_from_contact_line(lines)
        if loc:
            notes.append("Location read from the contact line (the place name next to the phone/email).")

    missing = [f for f, v in [("name", name), ("email", email), ("phone", phone), ("degree", degree),
                              ("cgpa", cgpa), ("skills", skills), ("experience", experience or None),
                              ("projects", projects), ("certifications", certifications), ("location", loc)] if not v]
    if not name:
        name = filename.rsplit(".", 1)[0] or "Unknown Candidate"
        notes.append("No name found; the file name is used instead.")

    return CandidateProfile(
        filename=filename, name=name, email=email, phone=phone, degree=degree, cgpa=cgpa,
        skills=skills, experience=experience, location=loc, projects=projects,
        certifications=certifications, missing_fields=missing, notes=notes,
    )
