"""Forward chaining: DATA-DRIVEN inference.

Start with the known facts. Repeatedly look for a rule whose premises are ALL
known; fire it and add its conclusion as a NEW fact. Stop when a full pass over
the rules produces nothing new (a "fixed point"). The goal is checked at the end.
"""
from __future__ import annotations

from backend.algorithms.knowledge_base import Rule


def forward_chain(initial_facts: dict[str, str], rules: list[Rule], goal: str = "eligible") -> dict:
    known = dict(initial_facts)
    fired: list[dict] = []
    fired_ids: set[str] = set()
    round_no = 0

    while True:
        round_no += 1
        progress = False
        for rule in rules:
            if rule.id in fired_ids or rule.conclusion in known:
                continue
            if all(p in known for p in rule.premises):
                known[rule.conclusion] = f"Derived by {rule.id}"
                fired_ids.add(rule.id)
                fired.append({"round": round_no, "rule": rule.id, "text": rule.text,
                              "premises": list(rule.premises), "derived": rule.conclusion})
                progress = True
        if not progress:
            break

    blocked = []
    for rule in rules:
        if rule.id not in fired_ids and rule.conclusion not in known:
            missing = [p for p in rule.premises if p not in known]
            blocked.append({"rule": rule.id, "text": rule.text, "derived": rule.conclusion, "missing": missing})

    return {
        "goal": goal,
        "goal_reached": goal in known,
        "initial_facts": list(initial_facts.keys()),
        "fired": fired,
        "blocked": blocked,
        "derived_facts": [f["derived"] for f in fired],
        "rounds": round_no - 1,
    }
