from backend.algorithms.bfs import bfs_eligibility
from backend.algorithms.criteria import build_eligibility_tree
from backend.algorithms.dfs import dfs_eligibility
from backend.models.schemas import CandidateProfile
from tests.helpers import sample_job


def cand(**kw):
    base = dict(id=1, name="T", degree="B.Tech", cgpa=8.6, skills=["Python", "Java", "SQL"], experience=2)
    base.update(kw)
    return CandidateProfile(**base)


def run(c, job=None):
    job = job or sample_job()
    return (bfs_eligibility(build_eligibility_tree(job, c)), dfs_eligibility(build_eligibility_tree(job, c)))


def test_eligible_candidate_passes_both():
    bfs, dfs = run(cand())
    assert bfs["eligible"] and dfs["eligible"]
    assert bfs["nodes_visited"] == dfs["nodes_visited"] == bfs["total_nodes"]
    assert not dfs["early_stopped"]


def test_bfs_visits_level_by_level():
    bfs, _ = run(cand())
    assert [s["id"] for s in bfs["order"]] == ["root", "academic", "experience", "skills",
                                              "degree", "cgpa", "skill:python", "skill:java", "skill:sql"]
    depths = [s["depth"] for s in bfs["order"]]
    assert depths == sorted(depths)  # never goes back up a level


def test_dfs_goes_deep_first():
    _, dfs = run(cand())
    assert [s["id"] for s in dfs["order"]] == ["root", "academic", "degree", "cgpa", "experience",
                                              "skills", "skill:python", "skill:java", "skill:sql"]


def test_dfs_stops_early_but_bfs_reports_everything():
    c = cand(degree="BCA", cgpa=6.0, experience=0)
    bfs, dfs = run(c)
    assert not bfs["eligible"] and not dfs["eligible"]
    assert dfs["early_stopped"] and dfs["stopped_at"] == "degree"
    assert dfs["nodes_visited"] < bfs["nodes_visited"]
    failed = {k["id"] for k in bfs["checks"] if k["status"] == "FAIL"}
    assert failed == {"degree", "cgpa", "experience"}


def test_missing_skill_fails():
    bfs, dfs = run(cand(skills=["Python", "Java"]))
    assert not bfs["eligible"] and not dfs["eligible"]
    assert [k["label"] for k in bfs["checks"] if k["status"] == "FAIL"] == ["Skill: SQL"]


def test_skill_matching_is_case_insensitive():
    bfs, _ = run(cand(skills=["python", "JAVA", "sql"]))
    assert bfs["eligible"]


def test_missing_cgpa_fails_instead_of_crashing():
    bfs, _ = run(cand(cgpa=None))
    assert not bfs["eligible"]
