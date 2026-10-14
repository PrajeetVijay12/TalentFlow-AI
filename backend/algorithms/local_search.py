"""Local search (steepest-ascent hill climbing) to improve the candidate ORDERING.

State      : an ordering (list) of candidates, starting from upload order.
Objective  : sum of  score_i / log2(position_i + 2)   (a DCG-style value: a high
             score near the top of the list counts MORE than the same score lower down).
Neighbour  : the same ordering with TWO ADJACENT candidates swapped.
Move rule  : look at every neighbour, take the one with the biggest objective gain;
             if no neighbour is strictly better we are at a local optimum -> stop.

This is NOT a sort() call: the ordering is improved one swap at a time and every
step is recorded so it can be shown in the UI.
"""
from __future__ import annotations

import math


def objective(order: list[int], scores: dict[int, float]) -> float:
    return sum(scores[cid] / math.log2(pos + 2) for pos, cid in enumerate(order))


def local_search(initial_order: list[int], scores: dict[int, float], names: dict[int, str] | None = None) -> dict:
    names = names or {}
    current = list(initial_order)
    cur_obj = objective(current, scores)
    steps = []
    max_iterations = max(1, len(current) ** 2)  # safety net; every move strictly improves so it ends sooner

    for it in range(1, max_iterations + 1):
        neighbours = []
        for i in range(len(current) - 1):
            cand = list(current)
            cand[i], cand[i + 1] = cand[i + 1], cand[i]
            val = objective(cand, scores)
            neighbours.append({"swap": [i, i + 1], "swapped": [names.get(current[i], current[i]), names.get(current[i + 1], current[i + 1])],
                               "objective": round(val, 4), "gain": round(val - cur_obj, 4), "order": cand})
        best = max(neighbours, key=lambda n: n["gain"], default=None)
        if best is None or best["gain"] <= 1e-9:
            steps.append({"iteration": it, "neighbours": [_public(n) for n in neighbours], "chosen": None,
                          "objective": round(cur_obj, 4), "order": list(current),
                          "message": "No neighbour improves the objective: local optimum reached."})
            break
        steps.append({"iteration": it, "neighbours": [_public(n) for n in neighbours], "chosen": _public(best),
                      "objective": round(best["objective"], 4), "order": list(best["order"]),
                      "message": f"Swapped positions {best['swap'][0] + 1} and {best['swap'][1] + 1} "
                                 f"({best['swapped'][0]} ↔ {best['swapped'][1]}), objective +{best['gain']:.4f}."})
        current, cur_obj = best["order"], best["objective"]

    return {
        "initial_order": list(initial_order),
        "final_order": current,
        "initial_objective": round(objective(initial_order, scores), 4),
        "final_objective": round(cur_obj, 4),
        "iterations": len([s for s in steps if s["chosen"]]),
        "steps": steps,
        "neighbour_definition": "Swap two adjacent candidates in the current ordering.",
    }


def _public(n: dict) -> dict:
    return {k: v for k, v in n.items() if k != "order"}
