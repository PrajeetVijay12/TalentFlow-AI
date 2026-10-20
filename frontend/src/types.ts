export interface Weights { skills: number; experience: number; projects: number; certifications: number }
export interface Thresholds { selected: number; waitlist: number }

export interface Job {
  title: string
  required_degrees: string[]
  degrees_equivalent: boolean
  min_cgpa: number
  min_experience: number
  required_skills: string[]
  required_certifications: string[]
  certifications_mandatory: boolean
  skills_mandatory: boolean
  location: string | null
  openings: number
  weights: Weights
  thresholds: Thresholds
}

export interface Project { name: string; category: string; score: number; evidence: string }

export interface Candidate {
  id: number
  filename: string
  name: string
  email: string | null
  phone: string | null
  degree: string | null
  cgpa: number | null
  skills: string[]
  experience: number
  location: string | null
  projects: Project[]
  certifications: string[]
  missing_fields: string[]
  notes: string[]
}

export interface UploadResult {
  filename: string
  status: 'ok' | 'duplicate' | 'error'
  message: string
  candidate?: Candidate
}

// ---- eligibility (BFS / DFS)
export interface CriteriaNode {
  id: string; label: string; status: string; leaf: boolean
  required: string | null; actual: string | null; detail: string | null
  children: CriteriaNode[]
}
export interface TraversalStep {
  step: number; id: string; label: string; depth: number; leaf: boolean; status: string
  required: string | null; actual: string | null; detail: string | null
}
export interface TraversalReport {
  algorithm: string; eligible: boolean; nodes_visited: number; total_nodes: number
  early_stopped: boolean; stopped_at: string | null
  order: TraversalStep[]; checks: { id: string; label: string; status: string; required: string; actual: string; detail: string }[]
  tree: CriteriaNode
}

// ---- heuristic
export interface ScorePart { score: number; weight: number; weighted: number; [k: string]: unknown }
export interface Heuristic {
  total: number
  formula: string
  parts: {
    skills: ScorePart & { matched: string[]; missing: string[]; required: number }
    experience: ScorePart & { candidate: number; required: number }
    projects: ScorePart & { best_project: string | null; category: string | null }
    certifications: ScorePart & { matched: string[]; missing: string[]; required: number }
  }
}

// ---- local search
export interface LSNeighbour { swap: number[]; swapped: string[]; objective: number; gain: number }
export interface LSStep { iteration: number; neighbours: LSNeighbour[]; chosen: LSNeighbour | null; objective: number; order: number[]; message: string }
export interface LocalSearch {
  initial_order: number[]; final_order: number[]; initial_objective: number; final_objective: number
  iterations: number; steps: LSStep[]; neighbour_definition: string; names: Record<string, string>
}

// ---- CSP
export interface CspResult {
  valid: boolean
  constraints: { name: string; constraint: string; candidate_value: string; hard: boolean; status: string }[]
  failed_hard: string[]; failed_soft: string[]; variables: number
  domains: Record<string, string[]>; nodes_explored: number; steps: string[]; solution: Record<string, string> | null
}

// ---- chaining
export interface FCResult {
  goal: string; goal_reached: boolean; initial_facts: string[]
  fired: { round: number; rule: string; text: string; premises: string[]; derived: string }[]
  blocked: { rule: string; text: string; derived: string; missing: string[] }[]
  derived_facts: string[]; rounds: number; rules: { id: string; text: string }[]
}
export interface ProofNode {
  goal: string; label: string; depth: number; status: string; via: string | null; reason: string; children: ProofNode[]
}
export interface BCResult { goal: string; proven: boolean; tree: ProofNode; steps: string[]; failed_requirements: string[] }

// ---- alpha-beta
export interface GameTreeNode {
  id: string; label: string; kind: 'MAX' | 'MIN' | 'LEAF'; visited: boolean; leaf_value: number | null
  pruned_by: string | null; alpha_in_text?: string; beta_in_text?: string
  alpha_out?: number | null; beta_out?: number | null; value?: number | null
  cutoff?: boolean; cutoff_reason?: string | null; pruned_children?: string[]
  children: GameTreeNode[]
}
export interface ABRound {
  round: number; value: number | null; winner: string | null; winner_candidate: number | null
  alpha_init: number; nodes_total: number; nodes_visited: number; nodes_pruned: number
  tree: GameTreeNode; child_values: Record<string, number>
}
export interface AlphaBeta {
  rounds: ABRound[]; picks: { candidate_id: number; round: number; robust_value: number }[]
  alpha_init: number; nodes_total: number; nodes_visited: number; nodes_pruned: number
}

// ---- simulated annealing
export interface SAStep {
  iteration: number; temperature: number; swap: number[]; swapped: string[]
  delta: number; accepted: boolean; worse_accepted: boolean; probability: number
  current_objective: number; best_objective: number
}
export interface SimulatedAnnealing {
  initial_order: number[]; final_order: number[]; initial_objective: number; final_objective: number
  iterations: number; accepted_moves: number; accepted_worse_moves: number; final_temperature: number
  T0: number; alpha: number; neighbour_definition: string; steps: SAStep[]; names: Record<string, string>
}

// ---- genetic algorithm
export interface GAEvent { generation: number; fitness: number; improvement: number; order: string[]; note: string }
export interface GeneticAlgorithm {
  initial_order: number[]; final_order: number[]; initial_fitness: number; best_fitness: number; improvement: number
  generations: number[]; population_size: number; num_generations: number
  crossover_rate: number; mutation_rate: number; events: GAEvent[]; names: Record<string, string>
}

// ---- resolution
export interface ResolutionClause { type: string; clause: string[]; source?: string; text?: string; id?: string }
export interface ResolutionStep { from_clauses: string[][]; resolvent: string[]; note: string }
export interface ResolutionResult {
  goal: string; proven: boolean; initial_clauses: number; total_clauses: number
  resolution_steps: ResolutionStep[]; cnf_clauses: ResolutionClause[]
  facts_used: number; rules_used: number; summary: string
}

export interface CandidateResult {
  id: number; name: string; profile: Candidate
  eligibility: { eligible: boolean; bfs: TraversalReport; dfs: TraversalReport; astar?: TraversalReport; agree: boolean; failed: string[]; passed: string[] }
  heuristic?: Heuristic
  local_search?: { initial_rank: number; final_rank: number; moved: boolean }
  csp: CspResult
  forward_chaining: FCResult
  backward_chaining: BCResult
  resolution?: ResolutionResult
  facts: Record<string, string>
  perspectives?: { id: string; label: string; score: number }[]
  alpha_beta: { status: string; selected: boolean; round: number | null; robust_value: number | null }
  final: { score: number | null; status: 'Selected' | 'Wait List' | 'Rejected'; reasons: string[]; eligible: boolean; csp_valid: boolean; rank: number }
}

export interface Stage { id: string; label: string; algorithm: string; input: number; output: number; ms: number; summary: string }
export interface RankRow { rank: number; id: number; name: string; score: number | null; status: 'Selected' | 'Wait List' | 'Rejected'; eligible: boolean }

export interface RunResult {
  job: Job
  summary: { total: number; eligible: number; csp_valid: number; Selected: number; 'Wait List': number; Rejected: number }
  stages: Stage[]
  ranking: RankRow[]
  candidates: CandidateResult[]
  heuristic_best_first: { step: number; id: number; h: number; frontier_size: number; name: string }[]
  local_search: LocalSearch | null
  simulated_annealing: SimulatedAnnealing | null
  genetic_algorithm: GeneticAlgorithm | null
  alpha_beta: AlphaBeta | null
}

export interface AlgoInfo {
  table: { algorithm: string; purpose: string; input: string; output: string; file: string }[]
  explanations: { title: string; body: string }[]
}

export interface JobOptions { titles: string[]; degrees: string[]; skills: string[]; certifications: string[]; locations: string[] }
export interface JdSuggestion { suggestion: Partial<Job>; found: string[]; not_found: string[] }

export type WorkflowStage = 'idle' | 'running' | 'complete'
export interface SampleResult { results: UploadResult[]; added: number; already_loaded: number; sample_job_applied: boolean }

export interface HistoryEntry {
  id: number; name: string; created: string; status: string
  candidates_count: number; title: string; location: string | null; openings: number
}
export interface HistoryDetail extends HistoryEntry { job: Job; run: RunResult | null }
