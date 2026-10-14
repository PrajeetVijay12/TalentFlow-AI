"""Deterministic normalization layer.

Resumes spell the same thing many ways ("B.Tech", "BTech", "Bachelor of
Technology"; "python", "PYTHON"). Before anything is compared, every value is
converted to ONE canonical spelling using plain dictionaries and regular
expressions. No machine learning or LLM is involved, so the same input always
gives the same output.
"""
from __future__ import annotations

import re

# ----------------------------------------------------------------- degrees
# (canonical name, regex). Order matters: more specific patterns first.
_DEGREE_PATTERNS: list[tuple[str, re.Pattern]] = [
    (name, re.compile(pat, re.IGNORECASE if not case else 0))
    for name, pat, case in [
        ("M.Tech", r"\bm\.?\s?tech\b|\bmasters?\s+(?:of|in)\s+technology\b", False),
        ("B.Tech", r"\bb\.?\s?tech\b|\bbachelors?\s+(?:of|in)\s+technology\b", False),
        ("M.E.", r"\bm\.\s?e\b\.?|\bmasters?\s+(?:of|in)\s+engineering\b", False),
        ("B.E.", r"\bb\.\s?e\b\.?|\bbachelors?\s+(?:of|in)\s+engineering\b", False),
        ("B.E.", r"\bBE\b", True),
        ("MCA", r"\bm\.?\s?c\.?\s?a\b|\bmasters?\s+(?:of|in)\s+computer\s+applications?\b", False),
        ("BCA", r"\bb\.?\s?c\.?\s?a\b|\bbachelors?\s+(?:of|in)\s+computer\s+applications?\b", False),
        ("MBA", r"\bm\.?\s?b\.?\s?a\b|\bmaster\s+of\s+business\s+administration\b", False),
        ("M.Sc", r"\bm\.?\s?sc\b|\bmasters?\s+(?:of|in)\s+science\b", False),
        ("B.Sc", r"\bb\.?\s?sc\b|\bbachelors?\s+(?:of|in)\s+science\b", False),
        ("B.Com", r"\bb\.?\s?com\b|\bbachelors?\s+(?:of|in)\s+commerce\b", False),
        ("PhD", r"\bph\.?\s?d\b|\bdoctorate\b", False),
        ("Diploma", r"\bdiploma\b", False),
    ]
]


def find_degree(text: str) -> str | None:
    """Return the canonical degree found inside free text, or None."""
    best: tuple[int, str] | None = None
    for name, pat in _DEGREE_PATTERNS:
        m = pat.search(text)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), name)
    return best[1] if best else None


def normalize_degree(text: str) -> str:
    """'BTech' / 'b.tech' / 'Bachelor of Technology' -> 'B.Tech'."""
    text = (text or "").strip()
    return find_degree(text) or text


def degree_key(text: str) -> str:
    return re.sub(r"[^a-z]", "", normalize_degree(text).lower())


# B.E. and B.Tech are equivalent four-year engineering degrees (likewise M.E. and M.Tech).
_EQUIVALENT_DEGREES = {"be": "btech", "me": "mtech"}


def degree_class(text: str, equivalent: bool = True) -> str:
    """Comparison key for a degree. With equivalent=True, B.E. and B.Tech share one key."""
    k = degree_key(text)
    return _EQUIVALENT_DEGREES.get(k, k) if equivalent else k


def degree_matches(candidate_degree: str | None, required: list[str], equivalent: bool = True) -> bool:
    """True if the candidate's degree is one of the accepted degrees (no accepted degrees = anything goes)."""
    if not required:
        return True
    if not candidate_degree:
        return False
    return degree_class(candidate_degree, equivalent) in {degree_class(d, equivalent) for d in required}


# ------------------------------------------------------------------ skills
_SKILL_ALIASES = {
    "python": "Python", "python3": "Python", "py": "Python",
    "java": "Java", "javascript": "JavaScript", "js": "JavaScript",
    "typescript": "TypeScript", "ts": "TypeScript",
    "sql": "SQL", "mysql": "MySQL", "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "mongodb": "MongoDB", "mongo": "MongoDB", "sqlite": "SQLite", "oracle": "Oracle",
    "c++": "C++", "cpp": "C++", "c#": "C#", "csharp": "C#", "c": "C", "golang": "Go",
    "r": "R", "kotlin": "Kotlin", "swift": "Swift", "php": "PHP", "ruby": "Ruby", "scala": "Scala",
    "html": "HTML", "html5": "HTML", "css": "CSS", "css3": "CSS",
    "react": "React", "reactjs": "React", "react.js": "React",
    "angular": "Angular", "vue": "Vue", "vue.js": "Vue",
    "node": "Node.js", "nodejs": "Node.js", "node.js": "Node.js",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "spring": "Spring", "spring boot": "Spring Boot", "springboot": "Spring Boot",
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "git": "Git", "github": "GitHub", "linux": "Linux", "bash": "Bash",
    "aws": "AWS", "azure": "Azure", "gcp": "GCP",
    "pandas": "Pandas", "numpy": "NumPy", "tensorflow": "TensorFlow",
    "machine learning": "Machine Learning", "data structures": "Data Structures",
    "rest": "REST", "rest api": "REST", "restful apis": "REST", "graphql": "GraphQL",
    "excel": "Excel", "tableau": "Tableau", "power bi": "Power BI",
}
# One-letter / very common words are only trusted inside an explicit Skills section.
_SCAN_EXCLUDE = {"c", "r", "py", "ts", "js", "rest"}

_SKILL_SCAN = [
    (alias, canon, re.compile(r"(?<![A-Za-z0-9+#])" + re.escape(alias) + r"(?![A-Za-z0-9+#])", re.IGNORECASE))
    for alias, canon in sorted(_SKILL_ALIASES.items(), key=lambda kv: -len(kv[0]))
    if alias not in _SCAN_EXCLUDE
]


def canonical_skill(text: str) -> str:
    """'python' / 'PYTHON' -> 'Python'. Unknown skills keep their spelling."""
    t = re.sub(r"\s+", " ", (text or "").strip(" \t.,;:-•*"))
    canon = _SKILL_ALIASES.get(t.lower())
    if canon:
        return canon
    return t.title() if t.islower() else t


def skill_key(text: str) -> str:
    return canonical_skill(text).lower()


def find_skills_in_text(text: str) -> list[str]:
    """Dictionary scan: every known skill mentioned in the text (in order of appearance)."""
    hits: list[tuple[int, str]] = []
    for _alias, canon, pat in _SKILL_SCAN:
        m = pat.search(text)
        if m:
            hits.append((m.start(), canon))
    seen: set[str] = set()
    out: list[str] = []
    for _pos, canon in sorted(hits):
        if canon not in seen:
            seen.add(canon)
            out.append(canon)
    return out


# ---------------------------------------------------------- certifications
_CERT_PATTERNS = [
    ("AWS", r"\baws\b|\bamazon\s+web\s+services\b"),
    ("Azure", r"\bazure\b|\bmicrosoft\s+certified\b"),
    ("GCP", r"\bgcp\b|\bgoogle\s+cloud\b"),
    ("Oracle", r"\boracle\b|\bocp\b"),
    ("PMP", r"\bpmp\b|\bproject\s+management\s+professional\b"),
    ("CCNA", r"\bccna\b"),
    ("Scrum", r"\bscrum\b|\bcsm\b"),
    ("Kubernetes", r"\bckad?\b|\bcertified\s+kubernetes\b"),
    ("Security+", r"\bsecurity\+"),
]
_CERT_COMPILED = [(n, re.compile(p, re.IGNORECASE)) for n, p in _CERT_PATTERNS]


def canonical_cert(text: str) -> str:
    """'AWS Certified Solutions Architect' -> 'AWS'."""
    t = re.sub(r"\s+", " ", (text or "").strip(" \t.,;:-•*"))
    for name, pat in _CERT_COMPILED:
        if pat.search(t):
            return name
    return t


def cert_key(text: str) -> str:
    return canonical_cert(text).lower()


# --------------------------------------------------------------- locations
_LOCATION_ALIASES = {
    "bangalore": "bengaluru", "bengaluru": "bengaluru", "bombay": "mumbai",
    "madras": "chennai", "gurgaon": "gurugram", "calcutta": "kolkata",
}


def location_key(text: str | None) -> str:
    """First place-name in 'Bangalore, Karnataka' -> 'bengaluru'."""
    if not text:
        return ""
    first = re.split(r"[,/|;]", text)[0].strip().lower()
    return _LOCATION_ALIASES.get(first, first)


def dedupe(items: list[str], keyfn) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for it in items:
        k = keyfn(it)
        if k and k not in seen:
            seen.add(k)
            out.append(it)
    return out


# ------------------------------------------------ option lists (for the UI dropdowns)
KNOWN_LOCATIONS = ["Bengaluru", "Chennai", "Hyderabad", "Mumbai", "Pune", "Delhi", "Noida", "Gurugram",
                   "Kolkata", "Ahmedabad", "Coimbatore", "Kochi", "Jaipur", "Chandigarh"]
JOB_TITLES = ["Software Engineer", "Backend Developer", "Frontend Developer", "Full Stack Developer", "Data Analyst",
              "Data Scientist", "Machine Learning Engineer", "DevOps Engineer", "QA / Test Engineer", "Mobile App Developer",
              "Cloud Engineer", "Product Developer", "Embedded Engineer", "Business Analyst"]


def known_skills() -> list[str]:
    return sorted(set(_SKILL_ALIASES.values()), key=str.lower)


def known_degrees() -> list[str]:
    out: list[str] = []
    for name, _ in _DEGREE_PATTERNS:
        if name not in out:
            out.append(name)
    return out


def known_certs() -> list[str]:
    return [n for n, _ in _CERT_PATTERNS]


def find_all_degrees(text: str) -> list[str]:
    """Every degree mentioned in the text (e.g. 'B.E / B.Tech' -> ['B.E.', 'B.Tech'])."""
    hits: list[tuple[int, str]] = []
    for name, pat in _DEGREE_PATTERNS:
        for m in pat.finditer(text):
            hits.append((m.start(), name))
    out: list[str] = []
    for _pos, name in sorted(hits):
        if name not in out:
            out.append(name)
    return out


def find_certs_in_text(text: str) -> list[str]:
    return [n for n, pat in _CERT_COMPILED if pat.search(text)]


_CANONICAL_CITY = {"bangalore": "Bengaluru", "bombay": "Mumbai", "madras": "Chennai", "gurgaon": "Gurugram",
                   "calcutta": "Kolkata"}


def find_location_in_text(text: str) -> str | None:
    """First known city mentioned in the text, normalized ('Bangalore' -> 'Bengaluru')."""
    best: tuple[int, str] | None = None
    for city in KNOWN_LOCATIONS + list(_LOCATION_ALIASES):
        m = re.search(r"\b" + re.escape(city) + r"\b", text, re.IGNORECASE)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), city)
    if not best:
        return None
    low = best[1].lower()
    return _CANONICAL_CITY.get(low, best[1].title())
