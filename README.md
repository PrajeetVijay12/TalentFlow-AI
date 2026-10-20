# TalentFlow AI — Resume Shortlisting with Classical AI

> **100% classical AI. Zero machine learning. Every decision is explainable.**

A full-stack HR tool that screens and ranks job applicants using 11 classical AI algorithms — search, constraint solving, logical inference, and game-tree optimization. Upload resumes, define a job, watch the pipeline run step-by-step, and get a fully reasoned shortlist.

---

## Features

| Feature | Details |
|---|---|
| **Resume parsing** | PDF & DOCX → structured data (name, degree, CGPA, skills, experience, projects, certs, location) |
| **11-stage pipeline** | BFS/DFS → heuristic → hill climbing + SA + GA → CSP → forward chaining → backward chaining → resolution → alpha-beta → game tree → ranking |
| **Live pipeline animation** | Watch each stage turn green in real time; skip animation any time |
| **Explainability** | Every score and decision is traced — see exactly why a candidate was selected or rejected |
| **Algorithm visualizer** | Interactive trace views for every algorithm (`/visualize`) |
| **Per-candidate reports** | Download a self-contained HTML report for any candidate (or all at once) |
| **CSV export** | Export the full ranked shortlist from the Ranking page |
| **3 test cases** | One-click launchers for SDE, Technician, and Content Writer (18+ sample candidates each) |
| **Secure accounts** | scrypt-hashed passwords, HttpOnly session cookies, rate-limited login, per-user data isolation |
| **Dark mode** | Toggle in sidebar, or `?theme=dark` in URL |

---

## Screenshots

| Pipeline running | Results page | Algorithm visualizer |
|---|---|---|
| Watch 11 stages animate | Cards with score ring + AI decision | BFS/DFS/Alpha-Beta traces |

---

## Architecture

```
frontend/  (React 19 + TypeScript + Vite)
│  src/pages/         — Upload, Job, Pipeline, Results, Ranking, CandidateDetail, Visualize …
│  src/components/    — ScoreRing, Badge, Avatar, WorkflowStepper, …
│  src/utils/         — reportGenerator.ts  (self-contained HTML reports)
└  styles.css

backend/   (FastAPI + SQLite)
│  parsing/           — text_extractor → resume_parser → normalizer
│  algorithms/        — 11 pure-Python classical AI modules (no web code inside)
│  services/          — pipeline.py, auth.py, database.py, upload_service.py
│  api/               — routes.py, auth_routes.py, testcase_routes.py
└  main.py            — FastAPI app (serves built frontend on same port)

test_cases/           — TC1 SDE (18 candidates), TC2 Technician (16), TC3 Content Writer (17)
tests/                — 100 pytest tests covering every algorithm and the full API
```

**Pipeline stages:**
`Parsing → BFS eligibility → DFS eligibility → Heuristic scoring → Hill climbing → Simulated annealing → Genetic algorithm → CSP → Forward chaining → Backward chaining → Resolution → Alpha-Beta game tree → Final ranking`

---

## Quick Start (existing install)

```bash
# From project root — builds frontend and serves everything on one port
cd frontend && npm run build && cd ..
uvicorn backend.main:app        # → http://127.0.0.1:8000
```

**Or double-click `start.bat`** — sets up venv + frontend on first run, then opens the browser automatically.

---

## New Device Setup Guide

### Prerequisites

| Tool | Version | Download |
|---|---|---|
| Python | 3.10 or newer | https://www.python.org/downloads/ |
| Node.js | 18 or newer | https://nodejs.org/ |
| Git | any | https://git-scm.com/ |

> **Windows users:** when installing Python, tick **"Add Python to PATH"** before clicking Install.

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/PrajeetVijay12/TalentFlow-AI.git
cd TalentFlow-AI
```

### Step 2 — Create Python virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Install frontend dependencies and build

```bash
cd frontend
npm install
npm run build
cd ..
```

### Step 5 — Start the server

```bash
uvicorn backend.main:app
```

Open **http://127.0.0.1:8000** in your browser.

> On Windows you can skip steps 2–5 by double-clicking **`start.bat`** — it does everything automatically on first run.

---

### Optional: Run in dev mode (hot reload)

```bash
# Terminal 1 — backend with auto-reload
uvicorn backend.main:app --reload

# Terminal 2 — frontend dev server (http://127.0.0.1:5173)
cd frontend && npm run dev
```

---

### Step 6 — Verify with tests

```bash
# Python tests (from project root, venv active)
python -m pytest -q

# Frontend type-check
cd frontend && npm run build
```

Expected: **100 tests passed**.

---

## Running Test Cases

Three pre-loaded test cases with 16–18 realistic candidates each. No manual uploads needed.

| File | Role | Candidates | Location | Openings |
|---|---|---|---|---|
| `Run_TC1_SDE.bat` | Software Development Engineer | 18 | Bengaluru | 3 |
| `Run_TC2_Technician.bat` | Hardware Technician | 16 | Any | 3 |
| `Run_TC3_ContentWriter.bat` | Content Writer | 17 | Mumbai | 2 |

**How to run:**
1. Double-click any `.bat` file (Windows)
2. The server starts automatically if not already running
3. Your browser opens, logs in as a demo account, loads the candidates, and starts the pipeline animation
4. Watch the pipeline run → Results page appears with all candidates ranked

**Manual (any OS):**
```bash
.venv\Scripts\python.exe test_cases\run_tc1.py   # Windows
# or
.venv/bin/python test_cases/run_tc1.py            # macOS / Linux
```

---

## Generating Per-Candidate Reports

On the **Results** page, click any candidate card → **Download Report** button in the top-left.  
On the **Ranking** page → **Download All Reports** button (exports every candidate as a ZIP of HTML files).

Reports are self-contained HTML files with all 11 pipeline stages, scores, traces, and a print-to-PDF button.

---

## Algorithm Reference

| Stage | Algorithm | What it does |
|---|---|---|
| 1 | **BFS eligibility** | Queue-based, full pass/fail report on all criteria |
| 2 | **DFS eligibility** | Stack-based, stops at first failed mandatory criterion |
| 3 | **Heuristic scoring** | Best-first expansion `h = 0.4·S + 0.3·E + 0.2·P + 0.1·C` |
| 4 | **Hill climbing** | Steepest-ascent swap-optimization of candidate ordering |
| 5 | **Simulated annealing** | Escapes local optima with temperature-based acceptance |
| 6 | **Genetic algorithm** | Population-based ordering optimization |
| 7 | **CSP** | Node consistency + backtracking with MRV heuristic |
| 8 | **Forward chaining** | Fact propagation through job-requirement rules |
| 9 | **Backward chaining** | Recursive goal-directed proof with full proof tree |
| 10 | **Resolution** | Clause-level logical refutation |
| 11 | **Alpha-Beta game tree** | Minimax with α/β pruning — robust shortlist selection |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Login (sets HttpOnly cookie) |
| `POST` | `/api/auth/logout` | Logout (deletes server-side session) |
| `GET` | `/api/auth/me` | Current user |
| `POST` | `/api/upload` | Upload PDF/DOCX resumes |
| `GET` | `/api/candidates` | List candidates |
| `GET/POST` | `/api/job` | Get or set job requirements |
| `POST` | `/api/pipeline/run` | Run the full 11-stage pipeline |
| `GET` | `/api/run/latest` | Latest pipeline run result |
| `GET` | `/api/run/history` | All past runs |
| `GET` | `/api/testcase/launch/{n}` | Load test case n, set cookie, redirect to pipeline |
| `GET` | `/api/health` | Health check |
| `GET` | `/docs` | Interactive API docs (Swagger UI) |

---

## Project Structure

```
TalentFlow-AI/
├── backend/
│   ├── algorithms/         11 classical AI modules
│   ├── api/                REST routes (main, auth, test cases)
│   ├── models/             Pydantic schemas
│   ├── parsing/            Resume text extraction and normalization
│   ├── services/           Pipeline, auth, database, uploads
│   └── main.py             FastAPI application entry point
├── frontend/
│   ├── src/
│   │   ├── pages/          React page components
│   │   ├── components/     Shared UI components
│   │   └── utils/          Report generator, helpers
│   └── dist/               Built frontend (served by FastAPI)
├── test_cases/             TC1/TC2/TC3 data + browser launchers
├── tests/                  100 pytest tests
├── sample_data/            10 sample resumes (PDF + DOCX)
├── Run_TC1_SDE.bat         One-click test case launcher
├── Run_TC2_Technician.bat
├── Run_TC3_ContentWriter.bat
├── start.bat               One-click full setup + launch (Windows)
└── requirements.txt
```

---

## Technologies

| Layer | Stack |
|---|---|
| Frontend | React 19, TypeScript, Vite, Recharts |
| Backend | Python 3.11, FastAPI, Uvicorn |
| Database | SQLite (Python standard library) |
| Resume parsing | pypdf, python-docx |
| Auth | scrypt (stdlib), HttpOnly cookies |
| Testing | pytest, httpx |

---

## Limitations

- Scanned / image-based PDFs cannot be parsed (no OCR)
- Multi-column PDFs with scrambled text order are only partially recovered
- Skill dictionary is finite; unknown spellings are kept as-is
- Project type is inferred from keywords; unlabelled projects default to "Mini"
- Open sign-up with no email verification or password reset
- Single-server SQLite (fine for demos and coursework; not for large deployments)

---

## License

Academic project — FOAI 389/386. Not licensed for commercial use.
