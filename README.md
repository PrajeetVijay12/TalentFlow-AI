# Resume Shortlisting System using Classical Artificial Intelligence

A web application that screens and ranks job applicants using **classical AI only** (search, constraint solving and logical inference). There is **no machine learning, no deep learning and no LLM** in any decision, and nothing is sent to an external service. Every score and decision can be explained.

## 1. Problem statement
Recruiters receive hundreds of resumes for one role. Reading them all is slow and inconsistent. This system automates the first screening round and, importantly, tells HR *why* each candidate was selected, wait-listed or rejected.

## 2. Objective
Accept a job description and many resumes → extract structured data → check eligibility → score → optimize the ranking → validate constraints → run logical inference → select candidates with game-tree search → produce an explainable ranked list.

## 3. Architecture
```
frontend (React + TypeScript + Vite)  ──/api──►  backend (FastAPI)
                                                   ├─ parsing/      PDF/DOCX text → structured candidate
                                                   ├─ algorithms/   pure-Python classical AI (no web code inside)
                                                   ├─ services/     pipeline orchestrator, SQLite, safe uploads
                                                   └─ api/routes.py REST endpoints
```
Algorithm files (`backend/algorithms/`): `criteria.py` (eligibility tree), `bfs.py`, `dfs.py`, `heuristic.py`, `local_search.py`, `csp.py`, `knowledge_base.py` (facts + rules), `forward_chaining.py`, `backward_chaining.py`, `game_tree.py`, `alpha_beta.py`.
Every algorithm returns a **trace** (steps taken) as well as a result; the UI draws those traces.

Pipeline (`backend/services/pipeline.py`):
`Parsing → BFS/DFS eligibility → Heuristic scoring → Local search → CSP → Forward chaining → Backward chaining → Alpha-Beta over the game tree → Final ranking → HR review`.
Candidates that fail eligibility never reach scoring/local search/Alpha-Beta (cheap checks first).

## 4. Technologies
Python 3.11, FastAPI, SQLite (standard library), pypdf, python-docx, pytest · React 19, TypeScript, Vite, Recharts.

## 5. Installation
Requires Python 3.10+ and Node 18+.
```bash
# from the project root
python -m venv .venv
.venv\Scripts\activate          # Windows   (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## 6. How to run
Two terminals, both from the project root:
```bash
# terminal 1 – backend (http://127.0.0.1:8000, API docs at /docs)
uvicorn backend.main:app --reload

# terminal 2 – frontend (http://127.0.0.1:5173)
cd frontend && npm run dev
```
Open http://127.0.0.1:5173, click **Load sample data**, then **Run pipeline**.

**Easiest way (one command / one click):** build the web app once, then the backend serves everything on one port.
```bash
cd frontend && npm install && npm run build && cd ..
uvicorn backend.main:app          # open http://127.0.0.1:8000
```
On Windows you can simply double-click **`start.bat`** — it sets everything up on first run and opens the browser.
Regenerate the sample resumes with `python sample_data/generate_samples.py`.

**Workflow:** after signing in, the app opens on the **file upload**. It is a guided 4-step flow shown as a progress bar on every page — **1 Resumes → 2 Job → 3 Run → 4 Review**. Upload the resumes, press **Start workflow**, and watch each of the 10 stages run and turn green one after another (with *Skip animation* if you are in a hurry). Job requirements can be reviewed before starting. The Overview page (`/overview`) shows the single next step to take.

**Job setup:** the Job page is built from dropdowns (degree, CGPA, experience, skills, certifications, location, thresholds). Every field is tagged *Must have* (pass/fail), *Adds to score* or *Decision rule*, with a live summary on the right. You can also paste a job description and the dropdowns are pre-filled by keyword matching (`POST /api/job/parse` — no AI model); it only suggests values for you to review.

**UI extras:** light theme by default with a dark-mode toggle in the sidebar (or `?theme=light` / `?theme=dark` in the URL); every algorithm tab has its own link, e.g. `/visualize?tab=ab` (Alpha-Beta), `tab=local`, `tab=csp`, `tab=forward`, `tab=backward`, `tab=heuristic`, `tab=bfs`; the Final Ranking page exports CSV.

## 7. How resume parsing works
1. `text_extractor.py` reads PDF (pypdf) or DOCX (python-docx, including tables). Corrupted, encrypted or empty files give a clear error.
2. `resume_parser.py` splits the text into **sections** by heading (Education, Skills, Experience, Projects, Certifications).
3. **Regular expressions and dictionaries** extract name, email, phone, degree, CGPA (also `/4` scale and percentages), skills, experience (explicit "2 years" or added-up date ranges), projects, certifications, location.
4. `normalizer.py` maps spellings to one canonical form (`python`/`PYTHON` → `Python`, `BTech`/`Bachelor of Technology` → `B.Tech`, `AWS Certified Solutions Architect` → `AWS`, `Bangalore` → `bengaluru`).
5. The place name in a contact line such as `Chennai | 9363389320 | name@mail.com` is used as the location when there is no `Location:` label.
6. Each field records a short note of *how* it was found. HR can correct any field in the UI.

## 8. BFS / DFS eligibility
Criteria form a tree: `Eligibility → Academic (Degree, CGPA) | Experience | Skills (one node per skill)`.
* **BFS** (queue) visits level by level and never stops early → a complete pass/fail report.
* **DFS** (stack) goes deep first and **stops at the first failed mandatory criterion**; the UI shows how many nodes it saved.
Both run for every candidate and must agree (a test checks this).

## 9. Heuristic search
`h(n) = 0.4·S + 0.3·E + 0.2·P + 0.1·C` (weights configurable). Eligible candidates are expanded **best-first** from a priority queue ordered by `h(n)`.

## 10. Local search
Steepest-ascent **hill climbing** over the candidate *ordering*. Neighbour = swap two adjacent candidates. Objective = Σ `score / log2(position+2)`. It starts from upload order, applies the best improving swap each iteration, and stops when no neighbour improves. Every iteration (all neighbours, gains, chosen swap) is shown.

## 11. CSP
Variables: degree, CGPA, experience, each required skill, each required certification, location. Domains hold the candidate's values. The solver applies **node consistency** (an empty domain means no solution) and **backtracking with the MRV heuristic**. *Hard* constraints eliminate; *soft* ones are only reported. Each constraint shows PASS/FAIL.

## 12. Forward chaining
Known facts (`has_skill(python)`, `experience_requirement_satisfied`, …) plus rules built from the job requirements (e.g. `skill_matched(all) → technical_skill`, `technical_skill ∧ experience → technical_fit`, `technical_fit ∧ academic_fit → eligible`). Rules fire until nothing new is derived. The UI shows the chain, and the rules that could not fire.

## 13. Backward chaining
Goal `eligible`. Recursively: is it a known fact, or does a rule conclude it whose premises can all be proven? The proof tree marks every sub-goal PROVEN/FAILED, so a failure names exactly what is missing (e.g. "Candidate has skill 'sql'").

## 14. Alpha-Beta pruning and 15. Game search tree
Hiring is not literally two-player, so it is modelled as a standard minimax tree:
* **Root = MAX** (HR picks a candidate).
* **Each candidate = MIN** node: a skeptical panel scores the candidate under 4 viewpoints (balanced, skills-first, experience-first, project-first); the candidate's value is its **worst** viewpoint (a robust choice).
* **Leaves** = those 4 scores.

Alpha-Beta keeps **α** (best value MAX is guaranteed, starting at the Wait List threshold) and **β**. When `β ≤ α` the remaining leaves of that MIN node are pruned. The UI shows α, β, the current node, cut-offs and pruned branches. The search repeats once per opening to choose the shortlist. Tests prove it returns the same value as plain minimax on 200 random trees while visiting fewer nodes.

## 16. Scoring formula
| Part | Formula |
|---|---|
| Skill | matched ÷ required × 100 |
| Experience | candidate ÷ required × 100, capped at 100 |
| Project | Major 100 · College Major 80 · Mini 60 (best project; none = 0) |
| Certification | matched ÷ required × 100 (no certs required = 100) |

Example: `0.4·80 + 0.3·80 + 0.2·80 + 0.1·25 = 74.5` (unit-tested).
**Status:** Selected = Alpha-Beta chose it **and** score ≥ Selected threshold; Wait List = between thresholds or openings full; Rejected = ineligible, CSP-hard-constraint violation, or score < Wait List threshold. Thresholds and openings are configurable.

## 17. Example workflow (sample data, location Bengaluru, 2 openings)
| Candidate | Profile | Outcome |
|---|---|---|
| Rahul Sharma | everything matches, major project, AWS | **Selected** (100) |
| Priya Nair | all skills, college major, no AWS | **Selected** (86) |
| Sneha Iyer | eligible, mini project, no cert | **Wait List** (82) |
| Vikram Rao | eligible but lives in Hyderabad | Rejected by **CSP** (location) |
| Arjun Mehta | missing SQL | Rejected by **BFS/DFS** |
| Neha Verma | 6 months experience | Rejected by **BFS/DFS** |
| Karan Singh | BCA, CGPA 6.4 | Rejected by **BFS/DFS** |

## 18. Testing
```bash
python -m pytest -q          # 100 tests
cd frontend && npm run build # type-check + production build
```
Tests cover normalization, parsing (real PDF and DOCX), BFS/DFS order and early stopping, the 74.5 example, local search, CSP, forward/backward chaining (and their agreement with the CSP), Alpha-Beta vs minimax, the full pipeline, thresholds, openings, and API upload/validation errors.

## Accounts and login
Every recruiter signs up with a name, email and password and only ever sees **their own** job, resumes and results.
* Passwords are stored only as salted **scrypt** hashes (Python standard library) — never in plain text.
* After login the browser gets a random session token in an **HttpOnly, SameSite=Lax** cookie (JavaScript cannot read it); the database stores only the SHA-256 of the token, so a leaked database cannot be used to log in. Sessions last 7 days; **Sign out** deletes the session on the server.
* Wrong email and wrong password give the **same** message; 5 failed attempts per email/IP block logins for 10 minutes.
* Every `/api/...` route except `/api/health` and `/api/auth/*` returns **401** without a valid session; one user can never read, edit or delete another user's candidates (they get 404).
* **Existing data:** resumes/jobs created before accounts existed are migrated automatically and adopted by the **first account that registers**.
* API: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`.

## Security and privacy
Only `.pdf`/`.docx` accepted, with magic-byte check and 5 MB limit; filenames sanitized; files stored under random names in `backend/uploads/` (never served); duplicates detected by SHA-256; resume text is never logged; no external API calls.

## 19. Limitations
* Parsing is rule-based: scanned (image) PDFs cannot be read, and multi-column PDFs whose text order is scrambled are only partly recovered (projects are rebuilt from lines shaped like "Name – description" and flagged in the extraction notes; the UI lets HR correct any field).
* The skill dictionary is finite; unknown skills are kept as written but spelling variants of them are not unified.
* Project type is guessed from keywords; unlabelled projects count as Mini (60).
* The game-tree "panel" is a modelling choice to demonstrate Alpha-Beta, not a real adversary.
* Accounts are basic: open sign-up, no email verification or password reset, and sessions are kept in the app's own SQLite database (fine for a single-server project, not for a large deployment).

## 20. Future improvements
Larger skill/synonym dictionaries, OCR for scanned PDFs, per-skill weights, CSV/PDF export of explanations, multi-job support, and a side-by-side candidate comparison view.
