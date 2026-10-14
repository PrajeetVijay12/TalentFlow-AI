"""Alpha-Beta pruning over the game tree built in game_tree.py.

Minimax: MAX nodes take the largest child value, MIN nodes the smallest.
Alpha-Beta computes the SAME answer but skips branches that cannot matter:

    alpha = the best value MAX is already guaranteed (starts at the threshold)
    beta  = the best value MIN is already guaranteed (starts at +infinity)

    * At a MIN node, as soon as a child value is <= alpha, MAX already has a better
      option elsewhere, so the REMAINING children are pruned (beta cut-off).
    * At a MAX node, if alpha >= beta the remaining children are pruned (alpha cut-off).

Starting alpha at the 'Wait List' threshold means: "I only care about candidates who
can beat the minimum acceptable score". Candidates whose worst-case value is not above
it are cut off immediately.
"""
from __future__ import annotations

import math

from backend.algorithms.game_tree import GameNode, build_selection_tree

INF = math.inf


def alpha_beta(node: GameNode, alpha: float, beta: float, rec: dict[str, dict]) -> float:
    r = rec[node.id] = {"id": node.id, "alpha_in": alpha, "beta_in": beta, "value": None,
                        "alpha_out": alpha, "beta_out": beta, "cutoff": False, "cutoff_reason": None,
                        "pruned": [], "best_child": None}
    if node.kind == "LEAF":
        r["value"] = node.value
        return node.value

    if node.kind == "MAX":
        v = -INF
        for i, child in enumerate(node.children):
            cv = alpha_beta(child, alpha, beta, rec)
            if cv > v:
                v, r["best_child"] = cv, child.id
            alpha = max(alpha, v)
            r["alpha_out"] = alpha
            if alpha >= beta:
                _prune(r, node.children[i + 1:], f"α ({_f(alpha)}) ≥ β ({_f(beta)})")
                break
    else:  # MIN
        v = INF
        for i, child in enumerate(node.children):
            cv = alpha_beta(child, alpha, beta, rec)
            if cv < v:
                v, r["best_child"] = cv, child.id
            beta = min(beta, v)
            r["beta_out"] = beta
            if beta <= alpha:
                _prune(r, node.children[i + 1:],
                       f"β ({_f(beta)}) ≤ α ({_f(alpha)}): MAX already has an equal or better option")
                break
    r["value"] = v
    return v


def _f(x: float) -> str:
    return "∞" if x == INF else "-∞" if x == -INF else f"{x:g}"


def _prune(r: dict, rest: list[GameNode], reason: str) -> None:
    if rest:
        r["cutoff"] = True
        r["cutoff_reason"] = reason
        r["pruned"] = [c.id for c in rest]


def _count(node: GameNode) -> int:
    return 1 + sum(_count(c) for c in node.children)


def serialize(node: GameNode, rec: dict[str, dict], pruned_by: str | None = None) -> dict:
    r = rec.get(node.id)
    out = {"id": node.id, "label": node.label, "kind": node.kind, "visited": r is not None,
           "leaf_value": node.value, "pruned_by": pruned_by}
    if r:
        out.update({k: (None if isinstance(r[k], float) and math.isinf(r[k]) else r[k])
                    for k in ("alpha_in", "beta_in", "alpha_out", "beta_out", "value", "cutoff", "cutoff_reason")})
        out["alpha_in_text"], out["beta_in_text"] = _f(r["alpha_in"]), _f(r["beta_in"])
        out["pruned_children"] = r["pruned"]
    kids = []
    for c in node.children:
        pb = pruned_by
        if pb is None and r and c.id in r["pruned"]:
            pb = node.id
        kids.append(serialize(c, rec, pb))
    out["children"] = kids
    return out


def run_alpha_beta(root: GameNode, alpha_init: float) -> dict:
    rec: dict[str, dict] = {}
    value = alpha_beta(root, alpha_init, INF, rec)
    best_id = rec["root"]["best_child"]
    winner = best_id if best_id and value > alpha_init else None
    total = _count(root)
    visited = len(rec)
    return {"value": None if value in (INF, -INF) else value, "winner": winner,
            "alpha_init": alpha_init, "nodes_total": total, "nodes_visited": visited,
            "nodes_pruned": total - visited, "tree": serialize(root, rec),
            "child_values": {c.id: rec[c.id]["value"] for c in root.children if c.id in rec}}


def select_candidates(entries: list[tuple[int, str, list[tuple[str, str, float]]]],
                      openings: int, alpha_init: float) -> dict:
    """Run Alpha-Beta in rounds. Each round selects ONE winner (best worst-case score),
    removes it, and searches again, up to `openings` rounds."""
    remaining = list(entries)
    rounds = []
    picks: list[dict] = []
    for rnd in range(1, openings + 1):
        if not remaining:
            break
        root = build_selection_tree(remaining)
        res = run_alpha_beta(root, alpha_init)
        res["round"] = rnd
        winner_id = res["winner"]
        if winner_id is None:
            res["winner_candidate"] = None
            rounds.append(res)
            break
        cid = int(winner_id[1:])
        res["winner_candidate"] = cid
        picks.append({"candidate_id": cid, "round": rnd, "robust_value": res["value"]})
        rounds.append(res)
        remaining = [e for e in remaining if e[0] != cid]
    return {"rounds": rounds, "picks": picks, "alpha_init": alpha_init,
            "nodes_total": sum(r["nodes_total"] for r in rounds),
            "nodes_visited": sum(r["nodes_visited"] for r in rounds),
            "nodes_pruned": sum(r["nodes_pruned"] for r in rounds)}
