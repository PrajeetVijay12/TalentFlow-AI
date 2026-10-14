"""Breadth-First Search over the eligibility criteria tree.

BFS uses a QUEUE (first in, first out). It visits the root, then ALL nodes one
level down, then ALL nodes two levels down, and so on. It never stops early, so
it always produces a COMPLETE report of every criterion that passed or failed.
"""
from __future__ import annotations

from collections import deque

from backend.algorithms.criteria import CheckResult, CriterionNode, build_report


def bfs_eligibility(root: CriterionNode) -> dict:
    queue: deque[tuple[CriterionNode, int]] = deque([(root, 0)])
    order: list[tuple[CriterionNode, int]] = []
    results: dict[str, CheckResult] = {}

    while queue:
        node, depth = queue.popleft()          # take from the FRONT
        order.append((node, depth))
        if node.is_leaf:
            results[node.id] = node.check()    # evaluate the criterion
        for child in node.children:
            queue.append((child, depth + 1))   # add to the BACK

    return build_report("BFS", root, order, results, stopped_at=None)
