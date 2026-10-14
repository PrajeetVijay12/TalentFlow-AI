"""Depth-First Search over the eligibility criteria tree, with EARLY TERMINATION.

DFS uses a STACK (last in, first out). It follows one branch all the way down
before trying the next branch. Because every criterion here is mandatory, the
moment one leaf FAILS the candidate cannot be eligible, so DFS stops at once and
skips the remaining nodes. That saves work for clearly unsuitable candidates.
"""
from __future__ import annotations

from backend.algorithms.criteria import CheckResult, CriterionNode, build_report


def dfs_eligibility(root: CriterionNode) -> dict:
    stack: list[tuple[CriterionNode, int]] = [(root, 0)]
    order: list[tuple[CriterionNode, int]] = []
    results: dict[str, CheckResult] = {}
    stopped_at = None

    while stack:
        node, depth = stack.pop()              # take from the TOP
        order.append((node, depth))
        if node.is_leaf:
            res = node.check()
            results[node.id] = res
            if not res.passed:                 # mandatory criterion failed -> stop now
                stopped_at = node.id
                break
        for child in reversed(node.children):  # reversed so the left-most child is popped first
            stack.append((child, depth + 1))

    return build_report("DFS", root, order, results, stopped_at=stopped_at)
