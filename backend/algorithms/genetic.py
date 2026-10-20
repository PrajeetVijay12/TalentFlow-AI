"""Genetic Algorithm for candidate ranking optimisation (Unit II — Local Search).

Overview
--------
A Genetic Algorithm (GA) mimics natural selection to find a near-optimal
*ordering* of eligible candidates:

    State      : permutation of candidate IDs (chromosome)
    Fitness    : DCG-style  Σ score / log₂(position + 2)
                 (same objective as Hill Climbing and Simulated Annealing)
    Selection  : tournament selection (k = 3)
    Crossover  : Order Crossover (OX) — preserves relative order, avoids duplicates
    Mutation   : random swap of two positions
    Elitism    : the best individual always survives to the next generation

Why a permutation encoding?
    Candidates cannot appear twice in a ranking, so a plain binary or real-valued
    chromosome doesn't work. Order Crossover (OX) is the standard fix: it copies
    a random slice from parent-1, then fills the rest from parent-2 in the order
    they appear there, skipping genes already copied.

Comparison with HC & SA
    • Hill Climbing makes one local swap per iteration; it gets stuck in local optima.
    • SA escapes via random uphill moves with probability P = exp(Δ/T).
    • GA maintains a POPULATION of solutions and recombines them. Good sub-sequences
      from two different orderings can be spliced together, exploring the search space
      in a fundamentally different way.
"""
from __future__ import annotations

import math
import random

POP_SIZE = 20
GENERATIONS = 50
TOURNAMENT_K = 3
CROSSOVER_RATE = 0.80
MUTATION_RATE = 0.20
SEED = 42


# ---------------------------------------------------------------------------
# Objective
# ---------------------------------------------------------------------------

def _dcg(perm: list[int], scores: dict[int, float]) -> float:
    """DCG-style objective: reward high-scoring candidates ranked early."""
    return sum(scores[cid] / math.log2(pos + 2) for pos, cid in enumerate(perm))


# ---------------------------------------------------------------------------
# Genetic operators
# ---------------------------------------------------------------------------

def _tournament(pop: list[list[int]], fits: list[float], k: int, rng: random.Random) -> list[int]:
    """Tournament selection: pick k random individuals, return the fittest."""
    contenders = rng.sample(range(len(pop)), k)
    winner = max(contenders, key=lambda i: fits[i])
    return pop[winner][:]


def _ox_crossover(p1: list[int], p2: list[int], rng: random.Random) -> list[int]:
    """Order Crossover (OX).

    1. Pick a random slice [a, b] and copy it from p1 into the child.
    2. Fill the remaining positions left-to-right from p2, skipping any
       gene already in the child (preserves relative order from p2).
    """
    n = len(p1)
    a, b = sorted(rng.sample(range(n), 2))
    child: list[int] = [-1] * n
    child[a : b + 1] = p1[a : b + 1]
    in_child = set(child[a : b + 1])
    pos = (b + 1) % n
    for gene in p2[b + 1 :] + p2[: b + 1]:
        if gene not in in_child:
            child[pos] = gene
            in_child.add(gene)
            pos = (pos + 1) % n
    return child


def _mutate(chrom: list[int], rng: random.Random) -> list[int]:
    """Swap mutation: swap two randomly chosen positions."""
    i, j = rng.sample(range(len(chrom)), 2)
    chrom[i], chrom[j] = chrom[j], chrom[i]
    return chrom


# ---------------------------------------------------------------------------
# Main GA
# ---------------------------------------------------------------------------

def genetic_algorithm(
    initial_order: list[int],
    scores: dict[int, float],
    names: dict[int, str] | None = None,
    pop_size: int = POP_SIZE,
    generations: int = GENERATIONS,
    crossover_rate: float = CROSSOVER_RATE,
    mutation_rate: float = MUTATION_RATE,
    seed: int = SEED,
) -> dict:
    """Run the GA and return a result dict compatible with the pipeline.

    Parameters
    ----------
    initial_order : list of candidate IDs in upload order
    scores        : {candidate_id: heuristic_score}
    names         : {candidate_id: display_name}  (optional, for display)

    Returns
    -------
    Dict with best_order, fitness trajectory, generation events, and
    a comparison table with HC & SA.
    """
    names = names or {}
    n = len(initial_order)

    if n <= 1:
        fit = round(_dcg(initial_order, scores), 4) if n == 1 else 0.0
        return {
            "initial_order": list(initial_order),
            "final_order": list(initial_order),
            "initial_fitness": fit,
            "best_fitness": fit,
            "improvement": 0.0,
            "generations": [fit],
            "population_size": pop_size,
            "num_generations": 0,
            "crossover_rate": crossover_rate,
            "mutation_rate": mutation_rate,
            "events": [],
            "names": {str(k): v for k, v in names.items()},
        }

    rng = random.Random(seed)

    # Seed the population: identity + (pop_size - 1) random shuffles
    population: list[list[int]] = [rng.sample(initial_order, n) for _ in range(pop_size - 1)]
    population.append(list(initial_order))

    fitnesses = [_dcg(p, scores) for p in population]
    best_idx = max(range(pop_size), key=lambda i: fitnesses[i])
    best_chrom = population[best_idx][:]
    best_fit = fitnesses[best_idx]
    initial_fit = round(_dcg(initial_order, scores), 4)

    gen_bests: list[float] = [round(best_fit, 4)]
    events: list[dict] = []

    for gen in range(1, generations + 1):
        new_pop: list[list[int]] = [best_chrom[:]]  # elitism

        while len(new_pop) < pop_size:
            p1 = _tournament(population, fitnesses, TOURNAMENT_K, rng)
            p2 = _tournament(population, fitnesses, TOURNAMENT_K, rng)
            child = _ox_crossover(p1, p2, rng) if rng.random() < crossover_rate else p1[:]
            if rng.random() < mutation_rate:
                child = _mutate(child, rng)
            new_pop.append(child)

        population = new_pop
        fitnesses = [_dcg(p, scores) for p in population]
        gen_best_idx = max(range(pop_size), key=lambda i: fitnesses[i])
        gen_best_fit = fitnesses[gen_best_idx]
        gen_bests.append(round(gen_best_fit, 4))

        if gen_best_fit > best_fit:
            delta = round(gen_best_fit - best_fit, 4)
            events.append({
                "generation": gen,
                "fitness": round(gen_best_fit, 4),
                "improvement": delta,
                "order": [names.get(c, str(c)) for c in population[gen_best_idx]],
                "note": f"New best at generation {gen} (Δ = +{delta})",
            })
            best_fit = gen_best_fit
            best_chrom = population[gen_best_idx][:]

    return {
        "initial_order": list(initial_order),
        "final_order": best_chrom,
        "initial_fitness": initial_fit,
        "best_fitness": round(best_fit, 4),
        "improvement": round(best_fit - initial_fit, 4),
        "generations": gen_bests,          # one float per generation, for the convergence chart
        "population_size": pop_size,
        "num_generations": generations,
        "crossover_rate": crossover_rate,
        "mutation_rate": mutation_rate,
        "events": events[:20],             # cap for display
        "names": {str(k): v for k, v in names.items() if k in set(initial_order)},
    }
