"""Text shown in the UI's 'Algorithm Explanation' page (kept in the backend so it lives next to the code)."""

ALGORITHM_TABLE = [
    {"algorithm": "BFS", "purpose": "Eligibility checking", "input": "Candidate + criteria tree", "output": "Eligibility result",
     "file": "algorithms/bfs.py"},
    {"algorithm": "DFS", "purpose": "Early eligibility checking", "input": "Candidate + criteria tree", "output": "Eligibility result",
     "file": "algorithms/dfs.py"},
    {"algorithm": "Heuristic Search", "purpose": "Candidate ranking", "input": "Candidate attributes", "output": "Score",
     "file": "algorithms/heuristic.py"},
    {"algorithm": "Local Search", "purpose": "Ranking optimization", "input": "Candidate ordering", "output": "Improved ordering",
     "file": "algorithms/local_search.py"},
    {"algorithm": "CSP", "purpose": "Constraint validation", "input": "Candidate + constraints", "output": "Valid / Invalid",
     "file": "algorithms/csp.py"},
    {"algorithm": "Forward Chaining", "purpose": "Data-driven inference", "input": "Facts + rules", "output": "Derived facts",
     "file": "algorithms/forward_chaining.py"},
    {"algorithm": "Backward Chaining", "purpose": "Goal-driven inference", "input": "Goal + rules", "output": "Verified / failed goal",
     "file": "algorithms/backward_chaining.py"},
    {"algorithm": "Alpha-Beta", "purpose": "Search pruning", "input": "Search tree", "output": "Best branch",
     "file": "algorithms/alpha_beta.py"},
    {"algorithm": "Game Tree", "purpose": "Candidate decision", "input": "Candidates", "output": "Selected branch",
     "file": "algorithms/game_tree.py"},
]

EXPLANATIONS = [
    {"title": "Resume parsing", "body": "Text is pulled out of the PDF/DOCX locally, split into sections (Education, Skills, Experience, Projects, Certifications) using heading names, and fields are extracted with regular expressions and dictionaries. A normalization layer makes 'python', 'PYTHON' and 'Python' equal and maps 'BTech' / 'Bachelor of Technology' to 'B.Tech'. No LLM is used, so the same resume always gives the same result."},
    {"title": "BFS and DFS", "body": "Eligibility criteria form a tree (Eligibility → Academic → Degree, CGPA; Experience; Skills → each skill). BFS uses a queue and checks level by level, always producing a full report. DFS uses a stack, goes deep first and stops as soon as a mandatory criterion fails, so it does less work for unsuitable candidates."},
    {"title": "Heuristic search", "body": "A heuristic estimates how good a candidate is: h(n) = 0.4·Skills + 0.3·Experience + 0.2·Projects + 0.1·Certifications (weights are configurable). A best-first search keeps candidates in a priority queue ordered by h(n) and always expands the most promising one first."},
    {"title": "Local search", "body": "Hill climbing on the candidate ORDER. A neighbour is the same list with two adjacent candidates swapped. The objective is the sum of score / log2(position + 2), which rewards putting high scores near the top. Each step moves to the best improving neighbour and stops when none improves (a local optimum)."},
    {"title": "Constraint satisfaction (CSP)", "body": "Each requirement is a variable (degree, CGPA, experience, each skill, location, certifications) with a domain of possible values and a constraint. The solver first removes impossible domain values (node consistency) and then runs a backtracking search. Hard constraints must hold; soft ones are only reported."},
    {"title": "Forward chaining", "body": "Starts from known facts (the candidate's skills, experience, etc.) and fires every IF-THEN rule whose conditions are all known, adding new facts, until nothing new appears. It shows how 'eligible = TRUE' is built up from the data."},
    {"title": "Backward chaining", "body": "Starts from the goal 'eligible?' and works backwards: which rule concludes it, and what must be true for that rule? Each sub-goal is checked recursively until facts are reached. If a sub-goal fails, the explanation names exactly which requirement is missing."},
    {"title": "Game search tree and Alpha-Beta pruning", "body": "Hiring is not literally a two-player game, so it is modelled as a classic minimax tree. The root is a MAX node (HR picks a candidate). Each candidate is a MIN node: a skeptical panel judges the candidate by its WORST score across four viewpoints (balanced, skills-first, experience-first, project-first). MAX wants the candidate with the best worst-case score. Alpha-Beta keeps two bounds: α (best value MAX is already guaranteed, starting at the Wait List threshold) and β (best MIN can force). When β ≤ α the rest of that branch cannot change the answer and is pruned. The search repeats once per opening to choose the shortlist."},
    {"title": "Final decision", "body": "Selected = chosen by Alpha-Beta and score ≥ the Selected threshold. Wait List = score between thresholds (or not chosen because openings are full). Rejected = ineligible, violates a hard constraint, or score below the Wait List threshold. All thresholds are configurable on the Job Requirements page."},
]
