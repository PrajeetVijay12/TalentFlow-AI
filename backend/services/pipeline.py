"""Runs the complete Classical-AI pipeline and builds the explanation for every candidate.

    Parsed candidates -> BFS/DFS/A* eligibility -> heuristic scoring -> hill climbing +
    simulated annealing -> CSP -> forward chaining -> backward chaining -> resolution ->
    Alpha-Beta -> final ranking
"""
from __future__ import annotations

import time

from backend.algorithms.alpha_beta import select_candidates
from backend.algorithms.astar import astar_eligibility
from backend.algorithms.backward_chaining import backward_chain
from backend.algorithms.bfs import bfs_eligibility
from backend.algorithms.criteria import build_eligibility_tree
from backend.algorithms.csp import solve_csp
from backend.algorithms.dfs import dfs_eligibility
from backend.algorithms.forward_chaining import forward_chain
from backend.algorithms.game_tree import perspective_scores
from backend.algorithms.heuristic import best_first_order, compute_score
from backend.algorithms.knowledge_base import build_facts, build_rules
from backend.algorithms.local_search import local_search
from backend.algorithms.resolution import resolution_prove
from backend.algorithms.simulated_annealing import simulated_annealing
from backend.models.schemas import CandidateProfile, JobRequirements


class _Timer:
    def __init__(self):
        self.t = time.perf_counter()

    def lap(self) -> float:
        now = time.perf_counter()
        ms, self.t = (now - self.t) * 1000, now
        return round(ms, 2)


def run_pipeline(job: JobRequirements, candidates: list[CandidateProfile]) -> dict:
    if not candidates:
        raise ValueError("No resumes uploaded.")
    tm = _Timer()
    by_id = {c.id: c for c in candidates}
    res: dict[int, dict] = {c.id: {"id": c.id, "name": c.name, "profile": c.model_dump()} for c in candidates}
    stages: list[dict] = []

    # --- Stage 1: parsing (already done at upload) ------------------------------------
    missing_any = sum(1 for c in candidates if c.missing_fields)
    stages.append({"id": "parsing", "label": "Resume Parsing", "algorithm": "Rule-based information extraction",
                   "input": len(candidates), "output": len(candidates), "ms": 0,
                   "summary": f"{len(candidates)} resumes parsed into structured data; {missing_any} had missing fields."})

    # --- Stage 2: BFS + DFS + A* eligibility ------------------------------------------------
    tm.lap()
    for c in candidates:
        tree = build_eligibility_tree(job, c)
        bfs = bfs_eligibility(tree)
        dfs = dfs_eligibility(build_eligibility_tree(job, c))
        astar = astar_eligibility(build_eligibility_tree(job, c))
        res[c.id]["eligibility"] = {"eligible": bfs["eligible"], "bfs": bfs, "dfs": dfs, "astar": astar,
                                    "agree": bfs["eligible"] == dfs["eligible"] == astar["eligible"],
                                    "failed": [k["label"] for k in bfs["checks"] if k["status"] == "FAIL"],
                                    "passed": [k["label"] for k in bfs["checks"] if k["status"] == "PASS"]}
    eligible = [c for c in candidates if res[c.id]["eligibility"]["eligible"]]
    saved = sum(res[c.id]["eligibility"]["bfs"]["nodes_visited"] - res[c.id]["eligibility"]["dfs"]["nodes_visited"] for c in candidates)
    astar_saved = sum(res[c.id]["eligibility"]["bfs"]["nodes_visited"] - res[c.id]["eligibility"]["astar"]["nodes_visited"] for c in candidates)
    stages.append({"id": "bfs_dfs", "label": "BFS / DFS / A* Eligibility", "algorithm": "BFS + DFS + A* (informed) Search",
                   "input": len(candidates), "output": len(eligible), "ms": tm.lap(),
                   "summary": f"{len(eligible)} of {len(candidates)} eligible. DFS skipped {saved} checks; A* skipped {astar_saved} checks vs BFS."})

    # --- Stage 3: heuristic scoring (eligible only) ---------------------------------
    scores: dict[int, float] = {}
    for c in eligible:
        r = compute_score(c, job)
        res[c.id]["heuristic"] = r
        scores[c.id] = r["total"]
    best_first = best_first_order(scores)
    stages.append({"id": "heuristic", "label": "Heuristic Search", "algorithm": "Weighted heuristic + best-first priority queue",
                   "input": len(eligible), "output": len(eligible), "ms": tm.lap(),
                   "summary": "Scored with h(n) = 0.4·S + 0.3·E + 0.2·P + 0.1·C (job weights)."})

    # --- Stage 4: local search (hill climbing) + simulated annealing ---------------
    names = {c.id: c.name for c in candidates}
    initial = [c.id for c in eligible]  # upload order
    ls = local_search(initial, scores, names) if eligible else None
    sa = simulated_annealing(initial, scores, names) if eligible else None
    if ls:
        for cid in initial:
            res[cid]["local_search"] = {"initial_rank": ls["initial_order"].index(cid) + 1,
                                        "final_rank": ls["final_order"].index(cid) + 1,
                                        "moved": ls["initial_order"].index(cid) != ls["final_order"].index(cid)}
    stages.append({"id": "local_search", "label": "Local Search", "algorithm": "Hill climbing (adjacent swaps) + Simulated Annealing",
                   "input": len(eligible), "output": len(eligible), "ms": tm.lap(),
                   "summary": (f"HC: {ls['iterations']} improving swap(s), obj {ls['initial_objective']}→{ls['final_objective']}. "
                               f"SA: {sa['accepted_moves']} accepted moves ({sa['accepted_worse_moves']} uphill), obj {sa['initial_objective']}→{sa['final_objective']}."
                               if ls and sa else "No eligible candidates to order.")})

    # --- Stage 5: CSP -----------------------------------------------------------------
    for c in candidates:
        res[c.id]["csp"] = solve_csp(job, c)
    survivors_ids = [cid for cid in (ls["final_order"] if ls else []) if res[cid]["csp"]["valid"]]
    csp_out = len(survivors_ids)
    stages.append({"id": "csp", "label": "Constraint Satisfaction", "algorithm": "CSP: node consistency + backtracking",
                   "input": len(eligible), "output": csp_out, "ms": tm.lap(),
                   "summary": f"{csp_out} of {len(eligible)} eligible candidates satisfy every hard constraint."})

    # --- Stage 6/7: forward & backward chaining -----------------------------------------
    rules = build_rules(job)
    for c in candidates:
        facts = build_facts(job, c)
        res[c.id]["forward_chaining"] = forward_chain(facts, rules)
        res[c.id]["forward_chaining"]["rules"] = [{"id": r.id, "text": r.text} for r in rules]
        res[c.id]["backward_chaining"] = backward_chain(facts, rules)
        res[c.id]["facts"] = facts
    fc_ok = sum(1 for c in candidates if res[c.id]["forward_chaining"]["goal_reached"])
    stages.append({"id": "forward_chaining", "label": "Forward Chaining", "algorithm": "Data-driven rule inference",
                   "input": len(candidates), "output": fc_ok, "ms": tm.lap(),
                   "summary": f"{fc_ok} candidates derived eligible = TRUE from their facts."})
    bc_ok = sum(1 for c in candidates if res[c.id]["backward_chaining"]["proven"])
    stages.append({"id": "backward_chaining", "label": "Backward Chaining", "algorithm": "Goal-driven rule inference",
                   "input": len(candidates), "output": bc_ok, "ms": tm.lap(),
                   "summary": f"{bc_ok} candidates had the goal 'eligible' proven."})

    # --- Stage 7b: Resolution Theorem Proving ------------------------------------------
    for c in candidates:
        facts = res[c.id]["facts"]
        res[c.id]["resolution"] = resolution_prove(facts, rules)
    res_ok = sum(1 for c in candidates if res[c.id]["resolution"]["proven"])
    stages.append({"id": "resolution", "label": "Resolution Theorem Proving", "algorithm": "Propositional resolution (refutation)",
                   "input": len(candidates), "output": res_ok, "ms": tm.lap(),
                   "summary": f"{res_ok} candidates proved eligible by refutation ({len(candidates) - res_ok} not proven)."})

    # --- Stage 8/9: Alpha-Beta over the game tree -------------------------------------
    entries = []
    for cid in survivors_ids:
        persp = perspective_scores(by_id[cid], job)
        res[cid]["perspectives"] = [{"id": p, "label": l, "score": s} for p, l, s in persp]
        entries.append((cid, by_id[cid].name, persp))
    ab = select_candidates(entries, job.openings, alpha_init=job.thresholds.waitlist) if entries else None
    picks = {p["candidate_id"]: p for p in (ab["picks"] if ab else [])}
    stages.append({"id": "alpha_beta", "label": "Alpha-Beta Pruning", "algorithm": "Alpha-Beta over the candidate game tree",
                   "input": len(entries), "output": len(picks), "ms": tm.lap(),
                   "summary": (f"Visited {ab['nodes_visited']} of {ab['nodes_total']} tree nodes; pruned {ab['nodes_pruned']}. "
                               f"{len(picks)} candidate(s) selected for {job.openings} opening(s).") if ab
                   else "No candidates reached the game tree."})
    stages.append({"id": "game_tree", "label": "Game Search Tree", "algorithm": "Minimax tree (MAX = HR, MIN = panel)",
                   "input": len(entries), "output": len(picks), "ms": 0,
                   "summary": "Each candidate is a MIN branch scored under 4 panel viewpoints; MAX picks the best worst-case."})

    # --- Stage 10: final decision and ranking ------------------------------------------
    th = job.thresholds
    for c in candidates:
        r = res[c.id]
        score = r.get("heuristic", {}).get("total")
        survived = c.id in survivors_ids
        reasons: list[str] = []
        elig = r["eligibility"]
        if not elig["eligible"]:
            status = "Rejected"
            reasons.append("Not eligible: failed " + ", ".join(elig["failed"]) + ".")
        elif not survived:
            status = "Rejected"
            reasons.append("Eligible on the core criteria but violated hard constraint(s): "
                           + ", ".join(r["csp"]["failed_hard"]) + ".")
        elif score < th.waitlist:
            status = "Rejected"
            reasons.append(f"Score {score} is below the Wait List threshold ({th.waitlist:g}).")
        elif c.id in picks and score >= th.selected:
            status = "Selected"
            reasons.append(f"Score {score} ≥ {th.selected:g} and Alpha-Beta chose this candidate in round {picks[c.id]['round']}.")
        elif score >= th.selected:
            status = "Wait List"
            reasons.append(f"Score {score} ≥ {th.selected:g}, but all {job.openings} opening(s) were filled by candidates with a stronger worst-case value.")
        else:
            status = "Wait List"
            reasons.append(f"Score {score} is between {th.waitlist:g} and {th.selected:g}.")
        if score is not None:
            h = r["heuristic"]["parts"]
            reasons.append(f"Skills {h['skills']['score']:g}, experience {h['experience']['score']:g}, projects {h['projects']['score']:g}, certifications {h['certifications']['score']:g}.")
        if r["csp"]["failed_soft"]:
            reasons.append("Soft preferences not met: " + ", ".join(r["csp"]["failed_soft"]) + ".")
        fc, bc = r["forward_chaining"]["goal_reached"], r["backward_chaining"]["proven"]
        reasons.append(f"Forward chaining: eligible = {str(fc).upper()}; backward chaining: goal {'proven' if bc else 'not proven'}.")

        if c.id in picks:
            ab_status = f"Selected in round {picks[c.id]['round']} (worst-case value {picks[c.id]['robust_value']})"
        elif c.id in survivors_ids:
            ab_status = "Searched, not selected"
        else:
            ab_status = "Not in game tree (eliminated earlier)"
        r["alpha_beta"] = {"status": ab_status, "selected": c.id in picks, "round": picks.get(c.id, {}).get("round"),
                           "robust_value": picks[c.id]["robust_value"] if c.id in picks else None}
        r["final"] = {"score": score, "status": status, "reasons": reasons, "eligible": elig["eligible"], "csp_valid": survived}

    order_selected = [cid for cid, _ in sorted(picks.items(), key=lambda kv: kv[1]["round"]) if res[cid]["final"]["status"] == "Selected"]
    ls_order = ls["final_order"] if ls else []
    rest_waitlist = [cid for cid in ls_order if res[cid]["final"]["status"] == "Wait List"]
    rest_rejected_scored = [cid for cid in ls_order if res[cid]["final"]["status"] == "Rejected"]
    unscored = sorted([c.id for c in candidates if c.id not in ls_order], key=lambda i: names[i])
    ranking_ids = order_selected + rest_waitlist + rest_rejected_scored + unscored
    ranking = []
    for rank, cid in enumerate(ranking_ids, start=1):
        res[cid]["final"]["rank"] = rank
        ranking.append({"rank": rank, "id": cid, "name": names[cid], "score": res[cid]["final"]["score"],
                        "status": res[cid]["final"]["status"], "eligible": res[cid]["final"]["eligible"]})
    counts = {s: sum(1 for r in ranking if r["status"] == s) for s in ("Selected", "Wait List", "Rejected")}
    stages.append({"id": "ranking", "label": "Final Ranking", "algorithm": "Threshold decision + ordering",
                   "input": len(candidates), "output": counts["Selected"], "ms": tm.lap(),
                   "summary": f"{counts['Selected']} selected, {counts['Wait List']} wait-listed, {counts['Rejected']} rejected."})

    return {
        "job": job.model_dump(),
        "summary": {"total": len(candidates), "eligible": len(eligible), "csp_valid": csp_out, **counts},
        "stages": stages,
        "ranking": ranking,
        "candidates": [res[c.id] for c in candidates],
        "heuristic_best_first": [{**s, "name": names[s["id"]]} for s in best_first],
        "local_search": ls and {**ls, "names": {str(k): v for k, v in names.items() if k in initial}},
        "simulated_annealing": sa and {**sa, "names": {str(k): v for k, v in names.items() if k in initial}},
        "alpha_beta": ab,
    }
