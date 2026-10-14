"""A* Search over the eligibility criteria tree (Unit II — Informed Search).

Key idea
--------
The criteria tree has a ROOT (Eligibility) with GROUP nodes (degree group,
experience group, …) that contain LEAF nodes (the actual checks).  We want to
decide whether a candidate is eligible as quickly as possible.

A* treats each node as a search state and uses

    f(n) = g(n) + h(n)

where
    g(n) = nodes already expanded (cost so far)
    h(n) = number of LEAF checks still hidden inside this node's subtree
           (admissible: it never overestimates the remaining work)

Because h(n) for a single leaf = 0, A* naturally reaches leaves before
expanding large group nodes.  The first FAILED leaf causes early termination
(just like DFS) but the order in which leaves are visited is guided by the
heuristic rather than being purely depth-first or purely breadth-first.

Contrast with the other two traversals:
  BFS  — visits every node level by level; no early stop; always complete.
  DFS  — goes deep-first; stops at the first failure; can miss failures in
          sibling branches that were never visited.
  A*   — expands in f(n) order; stops at the first failure; visits leaves
          of SMALLER subtrees before diving into larger ones, so it checks
          the most "decisive" (fewest remaining leaves) criteria first.
"""
from __future__ import annotations

import heapq

from backend.algorithms.criteria import CheckResult, CriterionNode, build_report


def _leaf_count(node: CriterionNode) -> int:
    """h(n): number of leaf nodes in this subtree (≥1 for leaves, ≥1 for groups)."""
    if node.is_leaf:
        return 1
    return sum(_leaf_count(c) for c in node.children)


def astar_eligibility(root: CriterionNode) -> dict:
    """Run A* over the eligibility tree and return a report in the same format as BFS/DFS."""
    order: list[tuple[CriterionNode, int]] = []
    results: dict[str, CheckResult] = {}
    counter = 0  # tiebreaker to avoid comparing CriterionNode objects

    # Heap entries: (f, g, counter, node, depth)
    heap: list[tuple[int, int, int, CriterionNode, int]] = []
    heapq.heappush(heap, (0 + _leaf_count(root), 0, counter, root, 0))

    stopped_at: str | None = None

    while heap:
        f, g, _, node, depth = heapq.heappop(heap)
        order.append((node, depth))

        if node.is_leaf:
            result = node.check()
            results[node.id] = result
            if not result.passed:
                stopped_at = node.id
                break           # early termination on first failure (admissible shortcut)
        else:
            new_g = g + 1
            for child in node.children:
                counter += 1
                new_h = _leaf_count(child)
                heapq.heappush(heap, (new_g + new_h, new_g, counter, child, depth + 1))

    return build_report("A*", root, order, results, stopped_at=stopped_at)
