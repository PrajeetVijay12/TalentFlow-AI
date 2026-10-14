"""Facts and IF-THEN rules shared by the forward- and backward-chaining engines.

A FACT is a string such as  has_skill(python)  or  technical_skill.
A RULE says: IF all premises are known facts THEN the conclusion is a new fact.

Facts come from the candidate's resume. Rules are built from the job requirements,
so changing the requirements changes the rules (nothing is hard-coded per candidate).
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.models.schemas import CandidateProfile, JobRequirements
from backend.parsing.normalizer import cert_key, degree_key, degree_matches, location_key, skill_key


@dataclass(frozen=True)
class Rule:
    id: str
    premises: tuple[str, ...]
    conclusion: str
    text: str  # human readable


def build_facts(job: JobRequirements, cand: CandidateProfile) -> dict[str, str]:
    """Return {fact: explanation} for everything known about the candidate."""
    facts: dict[str, str] = {}
    for s in cand.skills:
        facts[f"has_skill({skill_key(s)})"] = f"Resume lists skill {s}"
    for c in cand.certifications:
        facts[f"has_cert({cert_key(c)})"] = f"Resume lists certification {c}"
    facts[f"experience_years({cand.experience:g})"] = f"Resume shows {cand.experience:g} year(s) of experience"
    if cand.cgpa is not None:
        facts[f"cgpa({cand.cgpa:g})"] = f"Resume shows CGPA {cand.cgpa:g}"
    if cand.degree:
        facts[f"degree({degree_key(cand.degree)})"] = f"Resume shows degree {cand.degree}"

    # Facts obtained by comparing the resume with the requirements
    if degree_matches(cand.degree, job.required_degrees, job.degrees_equivalent):
        facts["degree_requirement_satisfied"] = f"{cand.degree or 'any degree'} satisfies the degree requirement"
    if job.min_cgpa <= 0 or (cand.cgpa is not None and cand.cgpa >= job.min_cgpa):
        facts["cgpa_requirement_satisfied"] = f"CGPA {cand.cgpa} >= {job.min_cgpa:g}"
    if cand.experience >= job.min_experience:
        facts["experience_requirement_satisfied"] = f"{cand.experience:g} yr >= {job.min_experience:g} yr"
    if not job.location or (cand.location and location_key(cand.location) == location_key(job.location)):
        facts["location_requirement_satisfied"] = f"Location {cand.location or 'n/a'} is acceptable"
    return facts


def build_rules(job: JobRequirements) -> list[Rule]:
    rules: list[Rule] = []
    n = 0

    def add(premises: list[str], conclusion: str, text: str) -> None:
        nonlocal n
        n += 1
        rules.append(Rule(f"R{n}", tuple(premises), conclusion, text))

    for s in job.required_skills:
        k = skill_key(s)
        add([f"has_skill({k})"], f"skill_matched({k})", f"IF candidate has {s} THEN skill {s} is matched")

    matched = [f"skill_matched({skill_key(s)})" for s in job.required_skills]
    if job.skills_mandatory:
        add(matched, "technical_skill", "IF ALL required skills are matched THEN technical_skill = true")
    else:  # any one matched skill is enough
        for m in matched:
            add([m], "technical_skill", f"IF {m} THEN technical_skill = true")

    add(["technical_skill", "experience_requirement_satisfied"], "technical_fit",
        "IF technical_skill AND experience requirement satisfied THEN technical_fit = true")
    add(["degree_requirement_satisfied", "cgpa_requirement_satisfied"], "academic_fit",
        "IF degree requirement AND CGPA requirement satisfied THEN academic_fit = true")

    elig_premises = ["technical_fit", "academic_fit"]
    elig_text = "IF technical_fit AND academic_fit"
    if job.location:
        elig_premises.append("location_requirement_satisfied")
        elig_text += " AND location satisfied"
    if job.certifications_mandatory and job.required_certifications:
        for c in job.required_certifications:
            add([f"has_cert({cert_key(c)})"], f"cert_matched({cert_key(c)})", f"IF candidate has {c} certification THEN {c} is matched")
        add([f"cert_matched({cert_key(c)})" for c in job.required_certifications], "certified",
            "IF ALL required certifications are matched THEN certified = true")
        elig_premises.append("certified")
        elig_text += " AND certified"
    add(elig_premises, "eligible", f"{elig_text} THEN eligible = true")
    return rules
