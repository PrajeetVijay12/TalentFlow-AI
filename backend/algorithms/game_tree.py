"""Game search tree for candidate selection (minimax-style).

Hiring is not literally a two-player game, so we model it as a classic
adversarial search tree that is academically defensible:

    ROOT  (MAX)  "HR picks the strongest candidate"
      ├── Candidate A (MIN)  "a skeptical panel judges A by its WORST viewpoint"
      │      ├── leaf: score under 'Balanced' weights
      │      ├── leaf: score under 'Skills-first' weights
      │      ├── leaf: score under 'Experience-first' weights
      │      └── leaf: score under 'Project-first' weights
      ├── Candidate B (MIN) ...
      └── ...

MAX wants the candidate whose worst-case panel score is highest (a robust choice).
Alpha-Beta (alpha_beta.py) searches this tree and prunes leaves that cannot change
the answer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from backend.algorithms.heuristic import compute_score
from backend.models.schemas import CandidateProfile, JobRequirements, Weights

# The "panel viewpoints": each one re-weights the same four scores.
PERSPECTIVES: list[tuple[str, str, Optional[Weights]]] = [
    ("balanced", "Balanced (HR weights)", None),  # None -> use the job's own weights
    ("skills", "Skills-first panel", Weights(skills=0.6, experience=0.2, projects=0.1, certifications=0.1)),
    ("experience", "Experience-first panel", Weights(skills=0.2, experience=0.5, projects=0.2, certifications=0.1)),
    ("projects", "Project-first panel", Weights(skills=0.2, experience=0.2, projects=0.5, certifications=0.1)),
]


@dataclass
class GameNode:
    id: str
    label: str
    kind: str                       # "MAX" | "MIN" | "LEAF"
    value: Optional[float] = None   # only leaves have a value up-front
    children: list["GameNode"] = field(default_factory=list)


def perspective_scores(cand: CandidateProfile, job: JobRequirements) -> list[tuple[str, str, float]]:
    out = []
    for pid, label, w in PERSPECTIVES:
        out.append((pid, label, compute_score(cand, job, w)["total"]))
    return out


def build_selection_tree(entries: list[tuple[int, str, list[tuple[str, str, float]]]]) -> GameNode:
    """entries = [(candidate_id, name, [(pid, label, score), ...]), ...]

    Move ordering matters for pruning: candidates are placed best-first (by their
    worst-case value) and each candidate's leaves worst-first. Good ordering lets
    Alpha-Beta prune much more. The tree built is exactly the same set of nodes.
    """
    root = GameNode("root", "All Candidates (HR chooses)", "MAX")
    ordered = sorted(entries, key=lambda e: -min(s for _, _, s in e[2]))
    for cid, name, leaves in ordered:
        node = GameNode(f"c{cid}", name, "MIN")
        for pid, label, score in sorted(leaves, key=lambda l: l[2]):
            node.children.append(GameNode(f"c{cid}:{pid}", label, "LEAF", value=round(score, 2)))
        root.children.append(node)
    return root
