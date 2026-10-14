"""Heuristic evaluation:  h(n) = w1*S + w2*E + w3*P + w4*C

S = skill score, E = experience score, P = project score, C = certification score
(each 0-100). Default weights: 40% / 30% / 20% / 10%.

A best-first search then expands candidates from a PRIORITY QUEUE ordered by h(n),
so the most promising candidate always comes out first.
"""
from __future__ import annotations

import heapq
from typing import Optional

from backend.models.schemas import CandidateProfile, JobRequirements, Weights
from backend.parsing.normalizer import cert_key, skill_key


def skill_score(cand: CandidateProfile, job: JobRequirements) -> dict:
    required = job.required_skills
    have = {skill_key(s) for s in cand.skills}
    matched = [s for s in required if skill_key(s) in have]
    missing = [s for s in required if skill_key(s) not in have]
    score = len(matched) / len(required) * 100 if required else 100.0
    return {"score": round(score, 2), "matched": matched, "missing": missing, "required": len(required)}


def experience_score(cand: CandidateProfile, job: JobRequirements) -> dict:
    if job.min_experience <= 0:
        score = 100.0
    else:
        score = min(cand.experience / job.min_experience * 100, 100.0)  # capped at 100
    return {"score": round(score, 2), "candidate": cand.experience, "required": job.min_experience}


def project_score(cand: CandidateProfile) -> dict:
    """Best project counts: Major = 100, College Major = 80, Mini = 60 (no projects = 0)."""
    if not cand.projects:
        return {"score": 0.0, "best_project": None, "category": None}
    best = max(cand.projects, key=lambda p: p.score)
    return {"score": float(best.score), "best_project": best.name, "category": best.category}


def certification_score(cand: CandidateProfile, job: JobRequirements) -> dict:
    required = job.required_certifications
    have = {cert_key(c) for c in cand.certifications}
    matched = [c for c in required if cert_key(c) in have]
    missing = [c for c in required if cert_key(c) not in have]
    score = len(matched) / len(required) * 100 if required else 100.0
    return {"score": round(score, 2), "matched": matched, "missing": missing, "required": len(required)}


def compute_score(cand: CandidateProfile, job: JobRequirements, weights: Optional[Weights] = None) -> dict:
    w = (weights or job.weights).normalized()
    s, e = skill_score(cand, job), experience_score(cand, job)
    p, c = project_score(cand), certification_score(cand, job)
    parts = {
        "skills": {**s, "weight": w.skills, "weighted": round(w.skills * s["score"], 2)},
        "experience": {**e, "weight": w.experience, "weighted": round(w.experience * e["score"], 2)},
        "projects": {**p, "weight": w.projects, "weighted": round(w.projects * p["score"], 2)},
        "certifications": {**c, "weight": w.certifications, "weighted": round(w.certifications * c["score"], 2)},
    }
    total = w.skills * s["score"] + w.experience * e["score"] + w.projects * p["score"] + w.certifications * c["score"]
    formula = (f"{w.skills:.2f}×{s['score']:g} + {w.experience:.2f}×{e['score']:g} + "
               f"{w.projects:.2f}×{p['score']:g} + {w.certifications:.2f}×{c['score']:g}")
    return {"total": round(total, 2), "parts": parts, "formula": formula}


def best_first_order(scores: dict[int, float]) -> list[dict]:
    """Best-first search: repeatedly pop the highest h(n) from a priority queue.

    Python's heapq is a MIN-heap, so we push -h to get the maximum first.
    Returns the expansion trace [{step, id, h, frontier_size}].
    """
    heap = [(-h, idx, cid) for idx, (cid, h) in enumerate(scores.items())]
    heapq.heapify(heap)
    trace = []
    while heap:
        size = len(heap)
        neg_h, _idx, cid = heapq.heappop(heap)
        trace.append({"step": len(trace) + 1, "id": cid, "h": -neg_h, "frontier_size": size})
    return trace
