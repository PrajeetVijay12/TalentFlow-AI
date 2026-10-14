"""
Knowledge-Based HR Query Agent  (Unit I · Unit IV — FOAI)

Architecture (classical AI):
  • Knowledge Base  = latest run result (candidates, scores, eligibility, chaining)
  • Inference Engine = rule/pattern matcher → intent dispatcher
  • Forward Chaining results are used to explain why someone WAS selected
  • Backward Chaining results are used to explain WHY a requirement failed
  • The agent is rational: it always maps a percept (query) to the best action (answer)
"""
from __future__ import annotations
import re
from typing import Optional

# ── formatting helpers ────────────────────────────────────────────────────────

def _fmt(v) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.1f}"
    except (TypeError, ValueError):
        return str(v)

def _emoji(status: str) -> str:
    return {"Selected": "✅", "Wait List": "⏳", "Rejected": "❌"}.get(status, "•")

def _one_liner(c: dict) -> str:
    e = _emoji(c["final"]["status"])
    return f"  {e} **{c['name']}** — Rank #{c['final']['rank']}, Score {_fmt(c['final']['score'])}, {c['final']['status']}"

def _profile(c: dict) -> str:
    p = c["profile"]
    lines = [
        f"**{c['name']}** {_emoji(c['final']['status'])} (Rank #{c['final']['rank']})",
        f"• Degree   : {p.get('degree') or '—'}",
        f"• CGPA     : {p.get('cgpa') or '—'}",
        f"• Experience: {p.get('experience', 0)} yr",
        f"• Location : {p.get('location') or 'Not specified'}",
    ]
    skills = p.get("skills", [])
    if skills:
        lines.append(f"• Skills   : {', '.join(skills[:7])}{'…' if len(skills) > 7 else ''}")
    certs = p.get("certifications", [])
    if certs:
        lines.append(f"• Certs    : {', '.join(certs[:4])}")
    lines.append(f"• AI Score : {_fmt(c['final']['score'])}")
    reasons = c["final"].get("reasons", [])
    if reasons:
        lines.append(f"• Decision : {reasons[0]}")
    return "\n".join(lines)

# ── candidate lookup ──────────────────────────────────────────────────────────

def _find(msg: str, candidates: list[dict]) -> Optional[dict]:
    """Return the candidate whose name (any part) best matches words in the message."""
    msg_l = msg.lower()
    best, best_len = None, 0
    for c in candidates:
        for part in c["name"].lower().split():
            if len(part) > 2 and part in msg_l and len(part) > best_len:
                best, best_len = c, len(part)
    return best

def _find_two(msg: str, candidates: list[dict]) -> list[dict]:
    """Return up to two distinct candidates found in the message."""
    msg_l = msg.lower()
    seen: set[int] = set()
    found: list[dict] = []
    # Order by name-length desc so "sharma" beats "sha"
    for c in sorted(candidates, key=lambda x: -len(x["name"])):
        if c["id"] in seen:
            continue
        for part in c["name"].lower().split():
            if len(part) > 2 and part in msg_l:
                found.append(c)
                seen.add(c["id"])
                break
        if len(found) == 2:
            break
    return found

# ── response builders ─────────────────────────────────────────────────────────

def _summary(run: dict, job: dict) -> str:
    s = run["summary"]
    t = job.get("title", "this role")
    lines = [
        f"**Screening Summary — '{t}'**",
        f"• Total applicants : {s.get('total', 0)}",
        f"• Eligible (BFS/DFS): {s.get('eligible', 0)}",
        f"• ✅ Shortlisted    : {s.get('Selected', 0)}",
        f"• ⏳ Wait List      : {s.get('Wait List', 0)}",
        f"• ❌ Rejected       : {s.get('Rejected', 0)}",
    ]
    th = job.get("thresholds", {})
    if th:
        lines.append(f"• Score thresholds : Shortlist ≥ {th.get('selected', 70)} | Waitlist ≥ {th.get('waitlist', 50)}")
    return "\n".join(lines)

def _list_status(candidates: list[dict], status: str) -> str:
    filtered = sorted([c for c in candidates if c["final"]["status"] == status],
                      key=lambda c: c["final"]["rank"])
    e = _emoji(status)
    if not filtered:
        return f"No candidates with status '{status}'."
    lines = [f"**{e} {status} candidates ({len(filtered)}):**"]
    lines += [_one_liner(c) for c in filtered]
    return "\n".join(lines)

def _top_n(candidates: list[dict], n: int) -> str:
    ranked = sorted(candidates, key=lambda c: c["final"]["rank"])[:n]
    if n == 1:
        c = ranked[0]
        p = c["profile"]
        lines = [
            f"**🏆 Top Candidate: {c['name']}** (Rank #1)",
            f"• Score : {_fmt(c['final']['score'])} | Status: {c['final']['status']}",
            f"• {p.get('degree') or '—'} | {p.get('experience', 0)} yr exp | CGPA {p.get('cgpa') or '—'}",
        ]
        skills = p.get("skills", [])
        if skills:
            lines.append(f"• Skills: {', '.join(skills[:5])}")
        reasons = c["final"].get("reasons", [])
        if reasons:
            lines.append(f"• Why: {reasons[0]}")
        return "\n".join(lines)
    lines = [f"**Top {n} candidates:**"]
    lines += [_one_liner(c) for c in ranked]
    return "\n".join(lines)

def _why_rejected(c: Optional[dict]) -> str:
    if not c:
        return "Include the candidate's name in your question — e.g. 'Why was Priya rejected?'"
    if c["final"]["status"] != "Rejected":
        return f"{c['name']} was not rejected — status is **{c['final']['status']}** (Rank #{c['final']['rank']})."
    lines = [f"**Why {c['name']} was ❌ Rejected:**"]
    # Eligibility (BFS / DFS)
    elig = c.get("eligibility", {})
    if not elig.get("eligible"):
        failed = elig.get("failed", [])
        lines.append(f"• Failed eligibility check ({len(failed)} criterion violated)")
        for f in failed[:4]:
            lines.append(f"  – {f}")
    # CSP hard constraints
    hard = c.get("csp", {}).get("failed_hard", [])
    if hard:
        lines.append(f"• CSP hard constraints failed: {', '.join(hard[:3])}")
    # Backward chaining — failed requirements
    bc_fails = c.get("backward_chaining", {}).get("failed_requirements", [])
    if bc_fails:
        lines.append(f"• Backward chaining: unmet prerequisites — {', '.join(bc_fails[:3])}")
    # Score
    s = c["final"].get("score")
    if s is not None:
        lines.append(f"• Final score {_fmt(s)} fell below rejection threshold")
    # AI reason
    r = c["final"].get("reasons", [])
    if r:
        lines.append(f"• AI reasoning: {r[0]}")
    return "\n".join(lines)

def _why_selected(c: Optional[dict]) -> str:
    if not c:
        return "Include the candidate's name — e.g. 'Why was Arjun selected?'"
    status = c["final"]["status"]
    e = _emoji(status)
    lines = [f"**Why {c['name']} is {e} {status}:**"]
    # Eligibility
    elig = c.get("eligibility", {})
    if elig.get("eligible"):
        passed = elig.get("passed", [])
        lines.append(f"• ✓ All {len(passed)} eligibility criteria passed (BFS/DFS)")
    # Forward chaining
    fc = c.get("forward_chaining", {})
    fired = fc.get("fired", [])
    if fired:
        lines.append(f"• ✓ Forward chaining fired {len(fired)} inference rules")
        if fired:
            lines.append(f"  – e.g. '{fired[0].get('text', '')}'" if fired else "")
    # Skills match
    h = c.get("heuristic") or {}
    parts = h.get("parts") or {}
    matched = (parts.get("skills") or {}).get("matched", [])
    if matched:
        lines.append(f"• ✓ Matched required skills: {', '.join(matched[:5])}")
    # Score
    lines.append(f"• ✓ Score: {_fmt(c['final']['score'])}")
    # Alpha-beta
    ab = c.get("alpha_beta") or {}
    if ab.get("selected"):
        lines.append(f"• ✓ Alpha-beta pruning confirmed selection (round {ab.get('round', '?')})")
    # Reason
    r = c["final"].get("reasons", [])
    if r:
        lines.append(f"• AI reasoning: {r[0]}")
    return "\n".join(lines)

def _compare(pair: list[dict]) -> str:
    if len(pair) < 2:
        return "I need two candidate names to compare. E.g. 'Compare Arjun and Neha'."
    c1, c2 = pair[0], pair[1]
    lines = [f"**{c1['name']} vs {c2['name']}:**", ""]
    rows = [
        ("Rank",   f"#{c1['final']['rank']}",                            f"#{c2['final']['rank']}"),
        ("Score",  _fmt(c1["final"]["score"]),                           _fmt(c2["final"]["score"])),
        ("Status", f"{_emoji(c1['final']['status'])} {c1['final']['status']}",
                   f"{_emoji(c2['final']['status'])} {c2['final']['status']}"),
        ("Degree", c1["profile"].get("degree") or "—",                   c2["profile"].get("degree") or "—"),
        ("CGPA",   str(c1["profile"].get("cgpa") or "—"),                str(c2["profile"].get("cgpa") or "—")),
        ("Exp",    f"{c1['profile'].get('experience', 0)} yr",            f"{c2['profile'].get('experience', 0)} yr"),
        ("Eligible","✓" if c1["eligibility"]["eligible"] else "✗",       "✓" if c2["eligibility"]["eligible"] else "✗"),
    ]
    n1, n2 = c1["name"].split()[0], c2["name"].split()[0]
    for label, v1, v2 in rows:
        lines.append(f"• **{label}**: {n1} → {v1}  |  {n2} → {v2}")
    s1 = c1["final"]["score"] or 0
    s2 = c2["final"]["score"] or 0
    winner = c1 if s1 >= s2 else c2
    lines.append(f"\n🏆 Higher score: **{winner['name']}** ({_fmt(max(s1, s2))})")
    return "\n".join(lines)

def _skill_query(skill: str, candidates: list[dict]) -> str:
    skill_l = skill.lower().strip()
    matched = sorted([c for c in candidates if any(skill_l in s.lower() for s in c["profile"].get("skills", []))],
                     key=lambda c: c["final"]["rank"])
    if not matched:
        return f"No candidates found with '{skill}' in their skill set."
    lines = [f"**Candidates with '{skill}' ({len(matched)}):**"]
    lines += [_one_liner(c) for c in matched]
    return "\n".join(lines)

def _job_req(job: dict) -> str:
    lines = [f"**Job: {job.get('title', 'Unknown Role')}**"]
    degs = job.get("required_degrees", [])
    if degs:
        lines.append(f"• Degrees   : {', '.join(degs)}")
    if job.get("min_cgpa"):
        lines.append(f"• Min CGPA  : {job['min_cgpa']}")
    if job.get("min_experience"):
        lines.append(f"• Min Exp   : {job['min_experience']} yr")
    skills = job.get("required_skills", [])
    if skills:
        mand = "mandatory" if job.get("skills_mandatory") else "preferred"
        lines.append(f"• Skills ({mand}): {', '.join(skills)}")
    certs = job.get("required_certifications", [])
    if certs:
        lines.append(f"• Certs     : {', '.join(certs)}")
    if job.get("location"):
        lines.append(f"• Location  : {job['location']}")
    lines.append(f"• Openings  : {job.get('openings', 1)}")
    th = job.get("thresholds", {})
    if th:
        lines.append(f"• Thresholds: Shortlist ≥ {th.get('selected', 70)} | Waitlist ≥ {th.get('waitlist', 50)}")
    return "\n".join(lines)

# ── intent table (pattern → tag) ──────────────────────────────────────────────

_INTENTS = [
    (r"\b(summary|overview|report|final results?|how did.+go)\b",               "summary"),
    (r"how many.*(eligible)",                                                    "count_elig"),
    (r"how many.*(select|shortlist)",                                            "count_sel"),
    (r"how many.*(reject)",                                                      "count_rej"),
    (r"how many.*(wait)",                                                        "count_wait"),
    (r"how many",                                                                "count_tot"),
    (r"(who|which).*(top|best|rank[ed]?\s*#?1|number.?one|highest scored?)",    "top_1"),
    (r"(top|best|first)\s*(candidate|ranked?|person|applicant)",                 "top_1"),
    (r"top\s*(\d+)",                                                             "top_n"),
    (r"rank[ed]?\s*#?\s*(\d+)",                                                  "rank_n"),
    (r"(list|show|who(?:m)?).*(select|shortlist)",                               "lst_sel"),
    (r"(list|show|who(?:m)?).*(wait.?list|waiting)",                             "lst_wait"),
    (r"(list|show|who(?:m)?).*(reject)",                                         "lst_rej"),
    (r"(list|show|all).*(candidate|applicant)",                                  "lst_all"),
    (r"why.*(reject)",                                                           "why_rej"),
    (r"why.*(select|chos|pick)",                                                 "why_sel"),
    (r"why.*(wait)",                                                             "why_sel"),
    (r"\bcompare\b",                                                             "compare"),
    (r"(who|which|candidates?).*(python|java(?:script)?|react|django|node|sql|"
     r"aws|docker|kubernetes|tensorflow|pytorch|c\+\+|typescript|fastapi|"
     r"flask|spring|machine.?learning|data.?science|angular|vue|linux|git)\b",  "tech_skill"),
    (r"(who|which).*(has|have|knows?|skilled?.+in|proficient)\s+(\w+)",         "skill_q"),
    (r"what.*(skills?|tech).*(does|has|do)\s+(\w+)",                            "cand_skills"),
    (r"skills?\s+of\s+(\w+)",                                                    "cand_skills"),
    (r"score[d]?\s*(?:above|over|more\s+than|greater\s+than|>)\s*(\d+\.?\d*)", "score_hi"),
    (r"score[d]?\s*(?:below|under|less\s+than|<)\s*(\d+\.?\d*)",               "score_lo"),
    (r"(highest|best|maximum|top)\s+score",                                     "max_score"),
    (r"(lowest|worst|minimum)\s+score",                                         "min_score"),
    (r"average\s+score",                                                        "avg_score"),
    (r"(\d+)\s*(?:\+\s*)?(?:years?|yrs?).*(experience|exp)\b",                 "exp_q"),
    (r"(?:experience|exp).+?(\d+)\s*(?:years?|yrs?)",                          "exp_q"),
    (r"cgpa\s*(?:above|over|>|≥)\s*(\d+\.?\d*)",                               "cgpa_hi"),
    (r"cgpa\s*(?:below|under|<)\s*(\d+\.?\d*)",                                "cgpa_lo"),
    (r"(?:from|in|based.?in|location)\s+([a-z]+(?:\s+[a-z]+)?)",               "loc_q"),
    (r"(job|role|position|requirement|criteria|what.*(need|want|looking))",     "job_req"),
    (r"(tell.+about|info.+about|who\s+is|describe|profile\s+of)\s+(\w+)",      "about"),
    (r"(who|what|tell).+(eligib)",                                              "elig_q"),
    (r"(csp|constraint)",                                                        "csp_q"),
    (r"(forward.?chain|backward.?chain)",                                        "chain_q"),
    (r"(algorithm|ai.?pipeline|stages?|how.+work)",                             "algo_q"),
]

# ── main entry point ──────────────────────────────────────────────────────────

def respond(message: str, run: dict, job: dict) -> str:
    msg  = message.lower().strip()
    cands = run.get("candidates", [])
    summ  = run.get("summary", {})

    for pattern, tag in _INTENTS:
        m = re.search(pattern, msg)
        if not m:
            continue

        if tag == "summary":
            return _summary(run, job)

        if tag == "count_tot":
            return f"There are **{summ.get('total', 0)} candidates** in this screening."
        if tag == "count_elig":
            return f"**{summ.get('eligible', 0)} of {summ.get('total', 0)}** candidates passed the BFS/DFS eligibility check."
        if tag == "count_sel":
            return f"**{summ.get('Selected', 0)} candidates** were shortlisted."
        if tag == "count_rej":
            return f"**{summ.get('Rejected', 0)} candidates** were rejected."
        if tag == "count_wait":
            return f"**{summ.get('Wait List', 0)} candidates** are on the wait list."

        if tag == "top_1":
            return _top_n(cands, 1)
        if tag == "top_n":
            n = min(int(m.group(1)), len(cands))
            return _top_n(cands, n)
        if tag == "rank_n":
            rank = int(m.group(1))
            c = next((x for x in cands if x["final"]["rank"] == rank), None)
            if not c:
                return f"No candidate at rank #{rank}."
            return _profile(c)

        if tag == "lst_sel":
            return _list_status(cands, "Selected")
        if tag == "lst_wait":
            return _list_status(cands, "Wait List")
        if tag == "lst_rej":
            return _list_status(cands, "Rejected")
        if tag == "lst_all":
            ranked = sorted(cands, key=lambda c: c["final"]["rank"])
            lines = [f"**All {len(ranked)} candidates (ranked):**"]
            lines += [_one_liner(c) for c in ranked]
            return "\n".join(lines)

        if tag == "why_rej":
            return _why_rejected(_find(msg, cands))
        if tag == "why_sel":
            return _why_selected(_find(msg, cands))

        if tag == "compare":
            return _compare(_find_two(msg, cands))

        if tag == "tech_skill":
            # Extract the technology name that triggered the match
            tech_pat = (r"(python|java(?:script)?|react|django|node(?:\.?js)?|sql|aws|docker|"
                        r"kubernetes|tensorflow|pytorch|c\+\+|typescript|fastapi|flask|spring|"
                        r"machine.?learning|data.?science|angular|vue|linux|git)")
            tm = re.search(tech_pat, msg)
            skill = tm.group(1) if tm else "that skill"
            return _skill_query(skill, cands)

        if tag == "skill_q":
            # Try to get a skill from after "has/knows/with"
            sm = re.search(r"(?:has|have|knows?|skilled?.+in|proficient.+in)\s+([a-z][a-z0-9+#.\s]{1,25}?)(?:\s+skill|\s+exp|\b)", msg)
            skill = sm.group(1).strip() if sm else ""
            if not skill:
                return "Which skill? E.g. 'Who knows Python?' or 'Who has React skills?'"
            return _skill_query(skill, cands)

        if tag == "cand_skills":
            c = _find(msg, cands)
            if not c:
                return "I couldn't identify the candidate. Try: 'What skills does Arjun have?'"
            skills = c["profile"].get("skills", [])
            if not skills:
                return f"{c['name']} has no skills listed."
            return f"**{c['name']}'s skills:** {', '.join(skills)}"

        if tag == "score_hi":
            try:
                th = float(m.group(1))
            except (IndexError, ValueError):
                return "Please specify a number, e.g. 'score above 75'."
            filt = sorted([c for c in cands if c["final"]["score"] is not None and c["final"]["score"] >= th],
                          key=lambda c: c["final"]["rank"])
            if not filt:
                return f"No candidates scored above {th}."
            lines = [f"**Candidates with score ≥ {th} ({len(filt)}):**"]
            lines += [_one_liner(c) for c in filt]
            return "\n".join(lines)

        if tag == "score_lo":
            try:
                th = float(m.group(1))
            except (IndexError, ValueError):
                return "Please specify a number, e.g. 'score below 60'."
            filt = sorted([c for c in cands if c["final"]["score"] is not None and c["final"]["score"] < th],
                          key=lambda c: c["final"]["rank"])
            if not filt:
                return f"No candidates scored below {th}."
            lines = [f"**Candidates with score < {th} ({len(filt)}):**"]
            lines += [_one_liner(c) for c in filt]
            return "\n".join(lines)

        if tag == "max_score":
            scored = [c for c in cands if c["final"]["score"] is not None]
            if not scored:
                return "No scores available."
            best = max(scored, key=lambda c: c["final"]["score"])
            return f"**Highest score: {best['name']}** — {_fmt(best['final']['score'])} (Rank #{best['final']['rank']})"

        if tag == "min_score":
            scored = [c for c in cands if c["final"]["score"] is not None]
            if not scored:
                return "No scores available."
            worst = min(scored, key=lambda c: c["final"]["score"])
            return f"**Lowest score: {worst['name']}** — {_fmt(worst['final']['score'])} (Rank #{worst['final']['rank']})"

        if tag == "avg_score":
            vals = [c["final"]["score"] for c in cands if c["final"]["score"] is not None]
            if not vals:
                return "No scores available."
            return f"**Average AI score: {sum(vals)/len(vals):.1f}** across {len(vals)} candidates."

        if tag == "exp_q":
            ym = re.search(r"(\d+)", msg)
            if ym:
                yrs = int(ym.group(1))
                filt = sorted([c for c in cands if c["profile"].get("experience", 0) >= yrs],
                              key=lambda c: c["final"]["rank"])
                if not filt:
                    return f"No candidates with {yrs}+ years of experience."
                lines = [f"**Candidates with ≥ {yrs} yr experience ({len(filt)}):**"]
                lines += [_one_liner(c) for c in filt]
                return "\n".join(lines)

        if tag == "cgpa_hi":
            try:
                val = float(m.group(1))
            except (IndexError, ValueError):
                return "Please specify a CGPA value, e.g. 'CGPA above 8'."
            filt = sorted([c for c in cands if c["profile"].get("cgpa") is not None and c["profile"]["cgpa"] >= val],
                          key=lambda c: c["final"]["rank"])
            if not filt:
                return f"No candidates with CGPA ≥ {val}."
            lines = [f"**Candidates with CGPA ≥ {val} ({len(filt)}):**"]
            lines += [_one_liner(c) for c in filt]
            return "\n".join(lines)

        if tag == "cgpa_lo":
            try:
                val = float(m.group(1))
            except (IndexError, ValueError):
                return "Please specify a CGPA value."
            filt = sorted([c for c in cands if c["profile"].get("cgpa") is not None and c["profile"]["cgpa"] < val],
                          key=lambda c: c["final"]["rank"])
            if not filt:
                return f"No candidates with CGPA < {val}."
            lines = [f"**Candidates with CGPA < {val} ({len(filt)}):**"]
            lines += [_one_liner(c) for c in filt]
            return "\n".join(lines)

        if tag == "loc_q":
            loc = m.group(1).strip()
            filt = sorted(
                [c for c in cands if c["profile"].get("location") and loc.lower() in c["profile"]["location"].lower()],
                key=lambda c: c["final"]["rank"],
            )
            if not filt:
                return f"No candidates from '{loc.title()}'."
            lines = [f"**Candidates from {loc.title()} ({len(filt)}):**"]
            lines += [_one_liner(c) for c in filt]
            return "\n".join(lines)

        if tag == "job_req":
            return _job_req(job)

        if tag == "about":
            c = _find(msg, cands)
            return _profile(c) if c else "I couldn't find that candidate. Try using their first or last name."

        if tag == "elig_q":
            elig = sorted([c for c in cands if c["eligibility"]["eligible"]],
                          key=lambda c: c["final"]["rank"])
            lines = [f"**Eligible candidates ({len(elig)}/{summ.get('total',0)}):**"]
            lines += [_one_liner(c) for c in elig]
            return "\n".join(lines)

        if tag == "csp_q":
            failed_csp = [c for c in cands if not c.get("csp", {}).get("valid", True)]
            if not failed_csp:
                return "All candidates passed CSP constraint validation."
            lines = [f"**Candidates who failed CSP ({len(failed_csp)}):**"]
            for c in failed_csp:
                hard = c.get("csp", {}).get("failed_hard", [])
                lines.append(f"  • {c['name']}: {', '.join(hard[:2]) if hard else 'soft constraint violation'}")
            return "\n".join(lines)

        if tag == "chain_q":
            if "forward" in msg:
                c = _find(msg, cands)
                if c:
                    fc = c.get("forward_chaining", {})
                    fired = fc.get("fired", [])
                    return (f"**Forward chaining for {c['name']}:**\n"
                            f"• Goal reached: {'✓' if fc.get('goal_reached') else '✗'}\n"
                            f"• Rules fired: {len(fired)}\n"
                            + ("\n".join(f"  – {r['text']}" for r in fired[:4])))
                return "Which candidate? E.g. 'forward chaining for Arjun'."
            if "backward" in msg:
                c = _find(msg, cands)
                if c:
                    bc = c.get("backward_chaining", {})
                    return (f"**Backward chaining for {c['name']}:**\n"
                            f"• Proven: {'✓' if bc.get('proven') else '✗'}\n"
                            + "\n".join(f"  – {s}" for s in bc.get("steps", [])[:5]))
                return "Which candidate? E.g. 'backward chaining for Priya'."
            return ("This system uses both:\n"
                    "• **Forward chaining** — fires IF-THEN rules on known facts to prove eligibility\n"
                    "• **Backward chaining** — starts from goal 'eligible?' and traces required premises")

        if tag == "algo_q":
            stages = run.get("stages", [])
            lines = [f"**AI Pipeline — {len(stages)} stages:**"]
            for i, s in enumerate(stages, 1):
                lines.append(f"  {i}. {s['label']} ({s['algorithm']}) → {s['output']} candidates out")
            return "\n".join(lines)

    # ── no intent matched: try a bare name lookup ──────────────────────────────
    c = _find(msg, cands)
    if c:
        return _profile(c)

    # ── fallback ───────────────────────────────────────────────────────────────
    return (
        "I can answer questions like:\n"
        "• **'Summary'** — overall results\n"
        "• **'Who is rank #1?'** — top candidate\n"
        "• **'Why was [name] rejected?'** — AI reasoning\n"
        "• **'Show selected candidates'** — shortlist\n"
        "• **'Who knows Python?'** — skill filter\n"
        "• **'Compare Arjun and Neha'** — side by side\n"
        "• **'Score above 75'** — score filter\n"
        "• **'Job requirements'** — active criteria\n"
        "• **'Forward chaining for [name]'** — logic trace"
    )
