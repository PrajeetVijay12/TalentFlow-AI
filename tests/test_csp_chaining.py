from backend.algorithms.backward_chaining import backward_chain
from backend.algorithms.csp import solve_csp
from backend.algorithms.forward_chaining import forward_chain
from backend.algorithms.knowledge_base import build_facts, build_rules
from backend.models.schemas import CandidateProfile
from tests.helpers import sample_job


def cand(**kw):
    base = dict(id=1, name="T", degree="B.Tech", cgpa=8.6, skills=["Python", "Java", "SQL"], experience=2,
                certifications=["AWS"], location="Bengaluru")
    base.update(kw)
    return CandidateProfile(**base)


# ---------------------------------------------------------------- CSP
def test_csp_all_pass():
    r = solve_csp(sample_job(), cand())
    assert r["valid"] and not r["failed_hard"]
    assert all(c["status"] == "PASS" for c in r["constraints"])


def test_csp_hard_failure_eliminates():
    r = solve_csp(sample_job(), cand(cgpa=6.0))
    assert not r["valid"] and r["failed_hard"] == ["CGPA"]
    assert any("EMPTY" in s for s in r["steps"])  # node consistency emptied the CGPA domain


def test_csp_location_constraint():
    r = solve_csp(sample_job(), cand(location="Hyderabad"))
    assert not r["valid"] and r["failed_hard"] == ["Location"]


def test_csp_soft_constraint_does_not_eliminate():
    r = solve_csp(sample_job(), cand(certifications=[]))
    assert r["valid"] and r["failed_soft"] == ["Certification AWS"]
    r2 = solve_csp(sample_job(certifications_mandatory=True), cand(certifications=[]))
    assert not r2["valid"]


def test_csp_backtracking_runs():
    r = solve_csp(sample_job(), cand())
    assert r["nodes_explored"] > 1 and r["solution"]["degree"] == "B.Tech"


# ---------------------------------------------------- forward chaining
def facts_rules(c, job=None):
    job = job or sample_job()
    return build_facts(job, c), build_rules(job)


def test_forward_chaining_derives_eligible_in_order():
    facts, rules = facts_rules(cand())
    r = forward_chain(facts, rules)
    assert r["goal_reached"]
    d = r["derived_facts"]
    assert d.index("technical_skill") < d.index("technical_fit") < d.index("eligible")
    assert "academic_fit" in d


def test_forward_chaining_blocked_when_skill_missing():
    facts, rules = facts_rules(cand(skills=["Python", "Java"]))
    r = forward_chain(facts, rules)
    assert not r["goal_reached"] and "technical_skill" not in r["derived_facts"]
    assert any("skill_matched(sql)" in b["missing"] for b in r["blocked"]) or \
        any("has_skill(sql)" in b["missing"] for b in r["blocked"])


def test_forward_chaining_reaches_fixed_point():
    facts, rules = facts_rules(cand())
    again = forward_chain({**facts, **{d: "x" for d in forward_chain(facts, rules)["derived_facts"]}}, rules)
    assert again["fired"] == []  # nothing new can be derived


# --------------------------------------------------- backward chaining
def test_backward_chaining_proves_goal():
    facts, rules = facts_rules(cand())
    r = backward_chain(facts, rules)
    assert r["proven"] and r["tree"]["status"] == "PROVEN" and r["failed_requirements"] == []


def test_backward_chaining_explains_failure():
    facts, rules = facts_rules(cand(skills=["Python", "Java"], experience=0))
    r = backward_chain(facts, rules)
    assert not r["proven"]
    assert "Candidate has skill 'sql'" in r["failed_requirements"]
    assert "Experience requirement" in r["failed_requirements"]


def test_forward_and_backward_agree_with_csp():
    job = sample_job()
    for c in [cand(), cand(skills=["Python"]), cand(location="Delhi"), cand(cgpa=5), cand(degree="BCA")]:
        facts = build_facts(job, c)
        rules = build_rules(job)
        fc = forward_chain(facts, rules)["goal_reached"]
        bc = backward_chain(facts, rules)["proven"]
        assert fc == bc == solve_csp(job, c)["valid"]
