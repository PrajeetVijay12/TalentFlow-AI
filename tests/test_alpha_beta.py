import math
import random

from backend.algorithms.alpha_beta import alpha_beta, run_alpha_beta, select_candidates
from backend.algorithms.game_tree import GameNode, build_selection_tree

INF = math.inf


def minimax(node):
    if node.kind == "LEAF":
        return node.value
    vals = [minimax(c) for c in node.children]
    return max(vals) if node.kind == "MAX" else min(vals)


def make_entries(table):
    """table = {id: [leaf scores]} -> entries understood by build_selection_tree"""
    return [(cid, f"C{cid}", [(f"p{i}", f"P{i}", s) for i, s in enumerate(scores)]) for cid, scores in table.items()]


def test_textbook_alpha_beta_tree_prunes_and_matches_minimax():
    # Classic example: MAX -> 3 MIN nodes with 3 leaves each.
    def mn(i, vals):
        return GameNode(f"m{i}", f"m{i}", "MIN", children=[GameNode(f"m{i}:{j}", "", "LEAF", value=v) for j, v in enumerate(vals)])
    root = GameNode("root", "root", "MAX", children=[mn(1, [3, 12, 8]), mn(2, [2, 4, 6]), mn(3, [14, 5, 2])])
    rec = {}
    value = alpha_beta(root, -INF, INF, rec)
    assert value == minimax(root) == 3
    assert rec["m2"]["cutoff"] and rec["m2"]["pruned"] == ["m2:1", "m2:2"]  # 2 <= alpha(3) -> rest pruned
    assert "m2:1" not in rec and "m2:2" not in rec
    assert rec["m2"]["alpha_in"] == 3 and rec["m3"]["alpha_in"] == 3


def test_alpha_beta_equals_minimax_on_random_trees():
    rng = random.Random(7)
    for _ in range(200):
        table = {i: [rng.randint(0, 100) for _ in range(4)] for i in range(1, rng.randint(2, 7))}
        root = build_selection_tree(make_entries(table))
        assert alpha_beta(root, -INF, INF, {}) == minimax(root)


def test_pruning_actually_reduces_work():
    table = {1: [90, 95, 99, 92], 2: [60, 70, 80, 90], 3: [50, 70, 85, 99]}
    res = run_alpha_beta(build_selection_tree(make_entries(table)), alpha_init=70)
    assert res["nodes_pruned"] > 0 and res["nodes_visited"] < res["nodes_total"]
    assert res["winner"] == "c1" and res["value"] == 90


def test_threshold_alpha_cuts_weak_candidates_immediately():
    table = {1: [90, 95], 2: [40, 99]}  # candidate 2's worst leaf (40) is below the threshold
    res = run_alpha_beta(build_selection_tree(make_entries(table)), alpha_init=70)
    c2 = next(n for n in res["tree"]["children"] if n["id"] == "c2")
    assert c2["cutoff"] and any(ch["pruned_by"] == "c2" for ch in c2["children"])


def test_no_winner_when_everyone_is_below_threshold():
    res = run_alpha_beta(build_selection_tree(make_entries({1: [50, 60], 2: [40, 65]})), alpha_init=70)
    assert res["winner"] is None


def test_select_candidates_runs_rounds_up_to_openings():
    table = {1: [90, 95], 2: [85, 99], 3: [80, 81], 4: [20, 99]}
    out = select_candidates(make_entries(table), openings=2, alpha_init=70)
    assert [p["candidate_id"] for p in out["picks"]] == [1, 2]
    assert [p["round"] for p in out["picks"]] == [1, 2]
    assert out["nodes_pruned"] > 0


def test_tree_records_alpha_beta_values_for_the_ui():
    res = run_alpha_beta(build_selection_tree(make_entries({1: [80, 90], 2: [70, 95]})), alpha_init=60)
    root = res["tree"]
    assert root["alpha_in"] == 60 and root["beta_in"] is None  # beta = +infinity
    assert all("alpha_in" in c for c in root["children"] if c["visited"])
