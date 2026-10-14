"""Simulated Annealing for candidate ranking optimisation (Unit II — Local Search in Continuous Spaces).

How it differs from Hill Climbing
----------------------------------
Hill climbing (adjacent-swap) always moves to the best neighbour; it
refuses any step that makes the objective worse.  This means it gets stuck
at the first LOCAL optimum it reaches.

Simulated Annealing (SA) escapes local optima by occasionally accepting a
WORSE solution with probability

    P(accept) = exp(Δ / T)

where Δ = new_objective − current_objective < 0  and T is the current
temperature.  At high T the algorithm explores freely.  As T decreases
(geometric cooling:  T ← α · T) it becomes increasingly greedy, converging
on the best solution found.

State      : an ordering (list) of candidate IDs.
Objective  : DCG-style  Σ score_i / log₂(position_i + 2)  (same as hill climbing).
Neighbour  : swap ANY two candidates, not just adjacent ones → larger search space.
Cooling    : T₀ = 1.0,  α = 0.90,  200 iterations.
"""
from __future__ import annotations

import math
import random


def _objective(order: list[int], scores: dict[int, float]) -> float:
    return sum(scores[cid] / math.log2(pos + 2) for pos, cid in enumerate(order))


def simulated_annealing(
    initial_order: list[int],
    scores: dict[int, float],
    names: dict[int, str] | None = None,
    T0: float = 1.0,
    alpha: float = 0.90,
    iterations: int = 200,
    seed: int = 42,
) -> dict:
    """
    Run SA on the candidate ordering.  Returns a dict with the same keys as
    local_search() so both can be rendered by the same UI component.
    """
    rng = random.Random(seed)          # deterministic so results are reproducible
    names = names or {}
    current = list(initial_order)
    cur_obj = _objective(current, scores)
    best = list(current)
    best_obj = cur_obj
    T = T0
    steps: list[dict] = []
    accepted_worse = 0
    total_accepted = 0

    for it in range(1, iterations + 1):
        n = len(current)
        if n < 2:
            break

        # Pick two distinct random positions (any pair, not just adjacent)
        a, b = rng.sample(range(n), 2)
        if a > b:
            a, b = b, a

        neighbor = list(current)
        neighbor[a], neighbor[b] = neighbor[b], neighbor[a]
        new_obj = _objective(neighbor, scores)
        delta = new_obj - cur_obj

        if delta > 0:
            # Always accept an improvement
            accept = True
        elif T > 1e-12:
            accept = rng.random() < math.exp(delta / T)
        else:
            accept = False

        if accept:
            total_accepted += 1
            if delta < 0:
                accepted_worse += 1
            current = neighbor
            cur_obj = new_obj
            if cur_obj > best_obj:
                best = list(current)
                best_obj = cur_obj

        # Record a snapshot every iteration (UI trims to first/last/key steps)
        steps.append({
            "iteration": it,
            "temperature": round(T, 5),
            "swap": [a, b],
            "swapped": [names.get(neighbor[a], str(neighbor[a])), names.get(neighbor[b], str(neighbor[b]))],
            "delta": round(delta, 4),
            "accepted": accept,
            "worse_accepted": accept and delta < 0,
            "probability": round(math.exp(delta / T), 4) if (delta < 0 and T > 1e-12) else (1.0 if delta >= 0 else 0.0),
            "current_objective": round(cur_obj, 4),
            "best_objective": round(best_obj, 4),
        })

        T *= alpha

    return {
        "initial_order": list(initial_order),
        "final_order": best,
        "initial_objective": round(_objective(initial_order, scores), 4),
        "final_objective": round(best_obj, 4),
        "iterations": iterations,
        "accepted_moves": total_accepted,
        "accepted_worse_moves": accepted_worse,
        "final_temperature": round(T, 8),
        "T0": T0,
        "alpha": alpha,
        "neighbour_definition": "Swap any two (non-adjacent) candidates in the current ordering.",
        "steps": steps,
        "names": {str(k): v for k, v in names.items() if k in set(initial_order)},
    }
