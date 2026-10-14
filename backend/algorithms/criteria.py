"""Eligibility criteria represented as a TREE (the search space for BFS and DFS).

                    Eligibility
          ┌────────────┼──────────────┐
      Academic      Experience       Skills
      ┌───┴───┐                   ┌────┼────┐
   Degree   CGPA               Python  Java  SQL

Leaf nodes are real checks. Group nodes pass only if ALL their children pass.
BFS and DFS (see bfs.py / dfs.py) differ in the ORDER they walk this tree and in
whether they may stop early.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from backend.models.schemas import CandidateProfile, JobRequirements
from backend.parsing.normalizer import degree_matches, skill_key


@dataclass
class CheckResult:
    required: str
    actual: str
    passed: bool
    detail: str


@dataclass
class CriterionNode:
    id: str
    label: str
    children: list["CriterionNode"] = field(default_factory=list)
    check: Optional[Callable[[], CheckResult]] = None

    @property
    def is_leaf(self) -> bool:
        return self.check is not None


def build_eligibility_tree(job: JobRequirements, cand: CandidateProfile) -> CriterionNode:
    def degree_check() -> CheckResult:
        req = " or ".join(job.required_degrees)
        if not cand.degree:
            return CheckResult(req, "not found", False, "No degree could be extracted from the resume.")
        ok = degree_matches(cand.degree, job.required_degrees, job.degrees_equivalent)
        same = job.degrees_equivalent and cand.degree not in job.required_degrees
        detail = ("Degree matches." if not same else f"{cand.degree} counts as the same degree as {req}.") if ok \
            else f"{cand.degree} is not one of the accepted degrees."
        return CheckResult(req, cand.degree, ok, detail)

    def cgpa_check() -> CheckResult:
        req = f">= {job.min_cgpa:g}"
        if cand.cgpa is None:
            return CheckResult(req, "not found", False, "No CGPA could be extracted from the resume.")
        ok = cand.cgpa >= job.min_cgpa
        return CheckResult(req, f"{cand.cgpa:g}", ok, "CGPA is high enough." if ok else f"CGPA {cand.cgpa:g} is below {job.min_cgpa:g}.")

    def exp_check() -> CheckResult:
        req = f">= {job.min_experience:g} yr"
        ok = cand.experience >= job.min_experience
        return CheckResult(req, f"{cand.experience:g} yr", ok,
                           "Enough experience." if ok else f"{cand.experience:g} yr is below the required {job.min_experience:g} yr.")

    def skill_check(skill: str) -> Callable[[], CheckResult]:
        def run() -> CheckResult:
            have = {skill_key(s) for s in cand.skills}
            ok = skill_key(skill) in have
            return CheckResult("required", "present" if ok else "missing", ok,
                               f"{skill} found on resume." if ok else f"Required skill {skill} is missing.")
        return run

    academic: list[CriterionNode] = []
    if job.required_degrees:
        academic.append(CriterionNode("degree", "Degree", check=degree_check))
    if job.min_cgpa > 0:
        academic.append(CriterionNode("cgpa", "CGPA", check=cgpa_check))

    root = CriterionNode("root", "Eligibility")
    if academic:
        root.children.append(CriterionNode("academic", "Academic Criteria", academic))
    root.children.append(CriterionNode("experience", "Experience", check=exp_check))
    if job.skills_mandatory and job.required_skills:
        root.children.append(CriterionNode(
            "skills", "Required Skills",
            [CriterionNode(f"skill:{skill_key(s)}", f"Skill: {s}", check=skill_check(s)) for s in job.required_skills]))
    return root


def count_nodes(node: CriterionNode) -> int:
    return 1 + sum(count_nodes(c) for c in node.children)


def _status(node: CriterionNode, results: dict[str, CheckResult], out: dict[str, str]) -> str:
    if node.is_leaf:
        st = "SKIPPED" if node.id not in results else ("PASS" if results[node.id].passed else "FAIL")
    else:
        kids = [_status(c, results, out) for c in node.children]
        st = "FAIL" if "FAIL" in kids else ("PASS" if all(k == "PASS" for k in kids) else "SKIPPED")
    out[node.id] = st
    return st


def build_report(algorithm: str, root: CriterionNode, order: list[tuple[CriterionNode, int]],
                 results: dict[str, CheckResult], stopped_at: Optional[str]) -> dict:
    """Common result format shared by BFS and DFS (the UI renders both the same way)."""
    statuses: dict[str, str] = {}
    _status(root, results, statuses)

    def nested(n: CriterionNode) -> dict:
        r = results.get(n.id)
        return {"id": n.id, "label": n.label, "status": statuses[n.id], "leaf": n.is_leaf,
                "required": r.required if r else None, "actual": r.actual if r else None,
                "detail": r.detail if r else None, "children": [nested(c) for c in n.children]}

    steps = []
    for i, (n, depth) in enumerate(order, start=1):
        r = results.get(n.id)
        steps.append({"step": i, "id": n.id, "label": n.label, "depth": depth, "leaf": n.is_leaf,
                      "status": statuses[n.id], "required": r.required if r else None,
                      "actual": r.actual if r else None, "detail": r.detail if r else None})
    checks = [{"id": n.id, "label": n.label, "status": statuses[n.id], "required": results[n.id].required,
               "actual": results[n.id].actual, "detail": results[n.id].detail}
              for n, _ in order if n.id in results]
    total = count_nodes(root)
    return {
        "algorithm": algorithm,
        "eligible": statuses["root"] == "PASS",
        "nodes_visited": len(order),
        "total_nodes": total,
        "early_stopped": stopped_at is not None,
        "stopped_at": stopped_at,
        "order": steps,
        "checks": checks,
        "tree": nested(root),
    }
