"""Resolution Theorem Proving (Unit IV — Logical Reasoning).

Overview
--------
Resolution is a REFUTATION-COMPLETE inference rule for propositional (and
first-order) logic.  To prove a goal G:

    1. Add the NEGATION of G to the knowledge base.
    2. Convert everything to Conjunctive Normal Form (CNF): a set of clauses,
       each clause being a disjunction of literals.
    3. Apply the resolution rule repeatedly:

           {A ∨ B}  ∧  {¬B ∨ C}   →   {A ∨ C}

    4. If the EMPTY CLAUSE {} is derived, a contradiction was found — the
       negation of G is unsatisfiable — so G is TRUE (proof by refutation).
    5. If no new clauses can be derived and the empty clause has not appeared,
       G cannot be proven from the current KB (open world assumption).

Mapping to HR eligibility
--------------------------
    Facts  → unit clauses  {fact}   e.g. {degree_requirement_satisfied}
    Rules  → IF p1 ∧ … ∧ pn THEN c   =   CNF clause  {¬p1 ∨ … ∨ ¬pn ∨ c}
    Goal   → "eligible"
    Refut  → add {¬eligible} and try to derive {}

The prover is propositional (all facts are propositional atoms), which is
exact for the eligibility domain used in this project.
"""
from __future__ import annotations

from typing import FrozenSet

from backend.algorithms.knowledge_base import Rule

# A clause is a frozen set of literal strings.
# Negation of literal "X" is represented as "~X"; "~~X" is NOT simplified
# (the KB does not generate double-negations).
Clause = FrozenSet[str]


def _neg(lit: str) -> str:
    return lit[1:] if lit.startswith("~") else f"~{lit}"


def _resolve(c1: Clause, c2: Clause) -> Clause | None:
    """Apply the resolution rule to two clauses.

    Finds the first complementary pair (L, ¬L) between the two clauses and
    returns the resolvent (the two clauses merged with that pair removed).
    Returns None when no complementary pair exists (clauses are unrelated).
    """
    for lit in c1:
        if _neg(lit) in c2:
            return (c1 - {lit}) | (c2 - {_neg(lit)})
    return None


def _cap_steps(steps: list[dict], cap: int) -> list[dict]:
    """Return at most `cap` steps, always keeping the last (proof) step if present."""
    if len(steps) <= cap:
        return steps
    # Always include the final step (which is the empty clause when proven)
    return steps[:cap - 1] + [steps[-1]]


def resolution_prove(
    facts: dict[str, str],
    rules: list[Rule],
    goal: str = "eligible",
    max_rounds: int = 300,
) -> dict:
    """Attempt to prove `goal` by resolution refutation.

    Parameters
    ----------
    facts   : {atom: explanation}  — initial known facts
    rules   : list of Rule objects from knowledge_base
    goal    : the propositional atom to prove (default "eligible")
    max_rounds : safety limit on resolution attempts

    Returns
    -------
    A dict with keys: proven, goal, initial_clauses, total_clauses,
    resolution_steps, summary, cnf_clauses (for display).
    """
    clauses: set[Clause] = set()
    cnf_display: list[dict] = []

    # 1. Facts → unit clauses {fact}
    for atom in facts:
        c: Clause = frozenset([atom])
        clauses.add(c)
        cnf_display.append({"type": "fact", "clause": list(c), "source": facts[atom]})

    # 2. Rules → implication clauses {¬p1, …, ¬pn, conclusion}
    for rule in rules:
        c = frozenset([_neg(p) for p in rule.premises] + [rule.conclusion])
        clauses.add(c)
        cnf_display.append({"type": "rule", "id": rule.id, "clause": list(c), "text": rule.text})

    # 3. Negation of goal → {¬goal}
    neg_goal: Clause = frozenset([_neg(goal)])
    clauses.add(neg_goal)
    cnf_display.append({"type": "negation", "clause": list(neg_goal),
                        "source": f"Refutation: assume ¬{goal}"})

    initial_count = len(clauses)
    clause_list = list(clauses)
    resolution_steps: list[dict] = []
    proven = False

    # 4. Saturation loop — each round tries all pairs (new × all); stops when
    #    the empty clause is derived or no new clauses are produced in a round.
    new_indices = list(range(len(clause_list)))   # indices added in the last round
    for _round in range(max_rounds):
        if not new_indices:
            break
        all_count = len(clause_list)
        added_this_round: list[int] = []

        for ni in new_indices:
            if proven:
                break
            for j in range(all_count):
                if ni == j:
                    continue
                resolvent = _resolve(clause_list[ni], clause_list[j])
                if resolvent is None:
                    continue
                if resolvent == frozenset():
                    resolution_steps.append({
                        "from_clauses": [list(clause_list[ni]), list(clause_list[j])],
                        "resolvent": [],
                        "note": "Empty clause — contradiction found. Goal PROVEN by refutation.",
                    })
                    proven = True
                    break
                if resolvent not in clauses:
                    resolution_steps.append({
                        "from_clauses": [list(clause_list[ni]), list(clause_list[j])],
                        "resolvent": list(resolvent),
                        "note": "New clause derived.",
                    })
                    clauses.add(resolvent)
                    clause_list.append(resolvent)
                    added_this_round.append(len(clause_list) - 1)
            if proven:
                break

        new_indices = added_this_round
        if proven:
            break

    return {
        "goal": goal,
        "proven": proven,
        "initial_clauses": initial_count,
        "total_clauses": len(clauses),
        "resolution_steps": _cap_steps(resolution_steps, 25),  # cap for display, always include proof step
        "cnf_clauses": cnf_display[:30],
        "facts_used": len(facts),
        "rules_used": len(rules),
        "summary": (
            f"Goal '{goal}' PROVEN by refutation after {len(resolution_steps)} resolution step(s)."
            if proven
            else f"Goal '{goal}' could not be proven ({len(clauses) - initial_count} new clauses derived, no contradiction)."
        ),
    }
