"""Constraint Satisfaction Problem (CSP) for hiring requirements.

A CSP has three parts:
  * VARIABLES   - things we need a value for (degree, cgpa, experience, location, each skill ...)
  * DOMAINS     - the values each variable may take. For one candidate the domain is the
                  value(s) that candidate actually has (taken from the resume).
  * CONSTRAINTS - rules the values must satisfy (degree must be B.Tech, CGPA >= 7.5 ...)

Solving = find an assignment of every variable that satisfies every HARD constraint.
Steps used here:
  1. Node consistency : remove domain values that break a constraint on a single variable.
                        A variable with an EMPTY domain means the problem has no solution.
  2. Backtracking search with the MRV heuristic (assign the variable with the smallest
     domain first) and constraint checking after each assignment.

Hard constraints must hold; soft constraints are reported (PASS/FAIL) but do not eliminate.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from backend.models.schemas import CandidateProfile, JobRequirements
from backend.parsing.normalizer import cert_key, degree_key, degree_matches, location_key, skill_key


@dataclass
class Constraint:
    name: str
    scope: tuple[str, ...]                    # variables the constraint talks about
    test: Callable[..., bool]                 # receives the values of the scope variables
    description: str
    hard: bool = True


class CSP:
    def __init__(self):
        self.domains: dict[str, list[Any]] = {}
        self.constraints: list[Constraint] = []
        self.steps: list[str] = []
        self.nodes_explored = 0

    def add_variable(self, name: str, domain: list[Any]) -> None:
        self.domains[name] = list(domain)

    def add_constraint(self, c: Constraint) -> None:
        self.constraints.append(c)

    # 1. node consistency -------------------------------------------------
    def enforce_node_consistency(self) -> None:
        for c in self.constraints:
            if len(c.scope) == 1 and c.hard:
                var = c.scope[0]
                before = self.domains[var]
                after = [v for v in before if c.test(v)]
                if len(after) != len(before):
                    self.steps.append(f"Node consistency: removed {len(before) - len(after)} value(s) from "
                                      f"domain of '{var}' because of '{c.name}'.")
                self.domains[var] = after
                if not after:
                    self.steps.append(f"Domain of '{var}' is EMPTY -> no solution can exist.")

    # 2. backtracking -----------------------------------------------------
    def _consistent(self, assignment: dict[str, Any]) -> bool:
        for c in self.constraints:
            if c.hard and all(v in assignment for v in c.scope):
                if not c.test(*[assignment[v] for v in c.scope]):
                    return False
        return True

    def backtrack(self, assignment: dict[str, Any] | None = None) -> dict[str, Any] | None:
        assignment = assignment or {}
        self.nodes_explored += 1
        if len(assignment) == len(self.domains):
            return assignment
        unassigned = [v for v in self.domains if v not in assignment]
        var = min(unassigned, key=lambda v: len(self.domains[v]))  # MRV heuristic
        for value in self.domains[var]:
            assignment[var] = value
            if self._consistent(assignment):
                result = self.backtrack(assignment)
                if result is not None:
                    return result
            self.steps.append(f"Backtrack: '{var}' = {value!r} violates a hard constraint.")
            del assignment[var]
        return None


def _fmt(v: Any) -> str:
    return "not found" if v is None else str(v)


def build_candidate_csp(job: JobRequirements, cand: CandidateProfile) -> tuple[CSP, dict[str, Any]]:
    csp = CSP()
    values: dict[str, Any] = {}  # the candidate's actual value for each variable (for display)

    csp.add_variable("degree", [cand.degree])
    values["degree"] = cand.degree
    csp.add_variable("cgpa", [cand.cgpa])
    values["cgpa"] = cand.cgpa
    csp.add_variable("experience", [cand.experience])
    values["experience"] = cand.experience
    have_skills = {skill_key(s) for s in cand.skills}
    for s in job.required_skills:
        csp.add_variable(f"skill:{s}", [skill_key(s) in have_skills])
        values[f"skill:{s}"] = skill_key(s) in have_skills
    have_certs = {cert_key(c) for c in cand.certifications}
    for c in job.required_certifications:
        csp.add_variable(f"cert:{c}", [cert_key(c) in have_certs])
        values[f"cert:{c}"] = cert_key(c) in have_certs
    if job.location:
        csp.add_variable("location", [cand.location])
        values["location"] = cand.location

    if job.required_degrees:
        same = " (B.E. = B.Tech)" if job.degrees_equivalent else ""
        csp.add_constraint(Constraint("Degree", ("degree",),
                                      lambda d: d is not None and degree_matches(d, job.required_degrees, job.degrees_equivalent),
                                      f"degree ∈ {{{', '.join(job.required_degrees)}}}{same}"))
    if job.min_cgpa > 0:
        csp.add_constraint(Constraint("CGPA", ("cgpa",), lambda g: g is not None and g >= job.min_cgpa,
                                      f"cgpa ≥ {job.min_cgpa:g}"))
    csp.add_constraint(Constraint("Experience", ("experience",), lambda e: e >= job.min_experience,
                                  f"experience ≥ {job.min_experience:g} yr"))
    for s in job.required_skills:
        csp.add_constraint(Constraint(f"Skill {s}", (f"skill:{s}",), lambda ok: ok is True,
                                      f"{s} required", hard=job.skills_mandatory))
    for c in job.required_certifications:
        csp.add_constraint(Constraint(f"Certification {c}", (f"cert:{c}",), lambda ok: ok is True,
                                      f"{c} certification", hard=job.certifications_mandatory))
    if job.location:
        want = location_key(job.location)
        csp.add_constraint(Constraint("Location", ("location",), lambda l: bool(l) and location_key(l) == want,
                                      f"location = {job.location}"))
    return csp, values


def solve_csp(job: JobRequirements, cand: CandidateProfile) -> dict:
    csp, values = build_candidate_csp(job, cand)

    # Evaluate every constraint on the candidate's real values for the PASS/FAIL table.
    table = []
    for c in csp.constraints:
        vals = [values[v] for v in c.scope]
        ok = bool(c.test(*vals))
        table.append({"name": c.name, "constraint": c.description, "candidate_value": ", ".join(_fmt(v) for v in vals),
                      "hard": c.hard, "status": "PASS" if ok else "FAIL"})

    domains_before = {k: [_fmt(x) for x in v] for k, v in csp.domains.items()}
    csp.enforce_node_consistency()
    solution = None if any(len(d) == 0 for d in csp.domains.values()) else csp.backtrack()
    failed_hard = [t for t in table if t["hard"] and t["status"] == "FAIL"]
    failed_soft = [t for t in table if not t["hard"] and t["status"] == "FAIL"]
    return {
        "valid": solution is not None,
        "constraints": table,
        "failed_hard": [t["name"] for t in failed_hard],
        "failed_soft": [t["name"] for t in failed_soft],
        "variables": len(csp.domains),
        "domains": domains_before,
        "nodes_explored": csp.nodes_explored,
        "steps": csp.steps[:40],
        "solution": None if solution is None else {k: _fmt(v) for k, v in solution.items()},
    }
