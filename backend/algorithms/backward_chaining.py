"""Backward chaining: GOAL-DRIVEN inference.

Start from a goal ("eligible"). A goal is TRUE if
  (a) it is already a known fact, or
  (b) some rule concludes it AND every premise of that rule can itself be proven
      (recursively, depth-first).
If a goal is neither a fact nor the conclusion of any rule, it FAILS, and the
failed leaf tells us exactly which requirement is missing.
All premises are checked (no early exit) so the explanation shows EVERY failure.
"""
from __future__ import annotations

from backend.algorithms.knowledge_base import Rule

_FRIENDLY = {
    "degree_requirement_satisfied": "Degree requirement",
    "cgpa_requirement_satisfied": "CGPA requirement",
    "experience_requirement_satisfied": "Experience requirement",
    "location_requirement_satisfied": "Location requirement",
}


def _describe(goal: str) -> str:
    if goal in _FRIENDLY:
        return _FRIENDLY[goal]
    if goal.startswith("has_skill("):
        return f"Candidate has skill '{goal[10:-1]}'"
    if goal.startswith("has_cert("):
        return f"Candidate has certification '{goal[9:-1]}'"
    return goal.replace("_", " ")


def backward_chain(facts: dict[str, str], rules: list[Rule], goal: str = "eligible") -> dict:
    steps: list[str] = []

    def prove(g: str, depth: int, path: tuple[str, ...]) -> dict:
        indent = "  " * depth
        node = {"goal": g, "label": _describe(g), "depth": depth, "status": "FAILED", "via": None,
                "reason": "", "children": []}
        if g in facts:
            node.update(status="PROVEN", via="known fact", reason=facts[g])
            steps.append(f"{indent}✔ {g}: known fact ({facts[g]})")
            return node
        if g in path:  # cycle guard
            node["reason"] = "circular dependency"
            return node
        supporting = [r for r in rules if r.conclusion == g]
        if not supporting:
            node["reason"] = "not a known fact and no rule can derive it"
            steps.append(f"{indent}✘ {g}: not a known fact and no rule derives it")
            return node
        steps.append(f"{indent}? {g}: try rule(s) {', '.join(r.id for r in supporting)}")
        failures: list[str] = []
        for rule in supporting:
            kids = [prove(p, depth + 1, path + (g,)) for p in rule.premises]
            node["children"].extend(kids)
            if all(k["status"] == "PROVEN" for k in kids):
                node.update(status="PROVEN", via=rule.id, reason=rule.text)
                steps.append(f"{indent}✔ {g}: proven by {rule.id}")
                return node
            failures += [k["label"] for k in kids if k["status"] != "PROVEN"]
        node["reason"] = "failed because: " + "; ".join(dict.fromkeys(failures))
        steps.append(f"{indent}✘ {g}: {node['reason']}")
        return node

    tree = prove(goal, 0, ())

    def leaf_failures(n: dict) -> list[str]:
        if n["status"] == "PROVEN":
            return []
        if not n["children"]:
            return [n["label"]]
        out: list[str] = []
        for c in n["children"]:
            out += leaf_failures(c)
        return out

    return {"goal": goal, "proven": tree["status"] == "PROVEN", "tree": tree, "steps": steps,
            "failed_requirements": list(dict.fromkeys(leaf_failures(tree)))}
