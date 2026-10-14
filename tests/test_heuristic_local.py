import math

import pytest

from backend.algorithms.heuristic import best_first_order, compute_score, experience_score
from backend.algorithms.local_search import local_search, objective
from backend.models.schemas import CandidateProfile, JobRequirements, Project


def test_spec_example_scores_74_5():
    job = JobRequirements(required_skills=["a", "b", "c", "d", "e"], min_experience=5,
                          required_certifications=["w", "x", "y", "z"])
    cand = CandidateProfile(name="X", skills=["a", "b", "c", "d"], experience=4,
                            projects=[Project(name="P", category="college_major", score=80)],
                            certifications=["w"])
    r = compute_score(cand, job)
    assert r["parts"]["skills"]["score"] == 80
    assert r["parts"]["experience"]["score"] == 80
    assert r["parts"]["projects"]["score"] == 80
    assert r["parts"]["certifications"]["score"] == 25
    assert r["total"] == 74.5


def test_experience_score_capped_at_100():
    job = JobRequirements(min_experience=1)
    assert experience_score(CandidateProfile(name="X", experience=10), job)["score"] == 100


def test_no_projects_scores_zero_and_best_project_counts():
    job = JobRequirements()
    assert compute_score(CandidateProfile(name="X"), job)["parts"]["projects"]["score"] == 0
    c = CandidateProfile(name="X", projects=[Project(name="a", score=60), Project(name="b", score=100, category="major")])
    assert compute_score(c, job)["parts"]["projects"]["score"] == 100


def test_weights_are_configurable():
    job = JobRequirements(weights={"skills": 1, "experience": 0, "projects": 0, "certifications": 0})
    c = CandidateProfile(name="X", skills=["Python"], experience=0)
    job.required_skills = ["Python", "Java"]
    assert compute_score(c, job)["total"] == 50


def test_best_first_pops_highest_first():
    trace = best_first_order({1: 70, 2: 95, 3: 80})
    assert [t["id"] for t in trace] == [2, 3, 1]


def test_local_search_improves_a_bad_ordering_step_by_step():
    scores = {1: 60, 2: 90, 3: 75, 4: 95}
    res = local_search([1, 2, 3, 4], scores)
    assert res["final_objective"] > res["initial_objective"]
    assert res["final_order"] == [4, 2, 3, 1]
    assert res["iterations"] >= 3               # it took several single swaps, not one sort
    for step in res["steps"]:
        if step["chosen"]:
            assert step["chosen"]["gain"] > 0   # every accepted move improves the objective
    assert res["steps"][-1]["chosen"] is None   # stops at a local optimum


def test_local_search_leaves_a_good_ordering_alone():
    res = local_search([2, 1], {1: 50, 2: 80})
    assert res["final_order"] == [2, 1] and res["iterations"] == 0


def test_objective_rewards_high_scores_near_top():
    s = {1: 90, 2: 50}
    assert objective([1, 2], s) > objective([2, 1], s)
    assert objective([1], s) == pytest.approx(90 / math.log2(2))


def test_local_search_single_and_empty():
    assert local_search([1], {1: 5})["final_order"] == [1]
    assert local_search([], {})["final_order"] == []
