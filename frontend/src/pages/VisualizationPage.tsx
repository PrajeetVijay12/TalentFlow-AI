import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Badge, Card, NeedRun, PageHead } from '../components/ui'
import { CriteriaTree, GameTree, ProofTree, TraversalTable } from '../components/trees'
import { ChainView } from '../components/chain'
import { useApp } from '../state'

const SLUGS: Record<string, number> = { bfs: 0, astar: 1, heuristic: 2, local: 3, sa: 4, csp: 5, forward: 6, backward: 7, resolution: 8, ab: 9 }
const TABS = ['BFS / DFS', 'A* Search', 'Heuristic', 'Local Search', 'Simulated Annealing', 'CSP', 'Forward Chaining', 'Backward Chaining', 'Resolution', 'Alpha-Beta & Game Tree'] as const

export default function VisualizationPage() {
  const { run } = useApp()
  const [params, setParams] = useSearchParams()
  const slug = params.get('tab') ?? 'bfs'
  const tab = TABS[SLUGS[slug] ?? 0]
  const setTab = (t: (typeof TABS)[number]) => setParams({ tab: Object.keys(SLUGS)[TABS.indexOf(t)] })
  const [cid, setCid] = useState<number | null>(null)
  const [round, setRound] = useState(0)
  if (!run) return <><PageHead title="Algorithm Visualization" /><NeedRun what="the visualizations" /></>

  const selId = cid ?? run.candidates[0].id
  const c = run.candidates.find(x => x.id === selId)!
  const perCandidate = ['BFS / DFS', 'A* Search', 'CSP', 'Forward Chaining', 'Backward Chaining', 'Resolution'].includes(tab)
  const names = Object.fromEntries(run.candidates.map(x => [x.id, x.name]))

  return (
    <>
      <PageHead eyebrow="Under the hood" title="Algorithm Visualization" desc="See each classical-AI algorithm working on the real data from the latest run." />
      <div className="tabs">{TABS.map(t => <button key={t} className={tab === t ? 'on' : ''} onClick={() => setTab(t)}>{t}</button>)}</div>
      {perCandidate && (
        <div className="row" style={{ marginBottom: 14 }}>
          <b>Candidate:</b>
          <select style={{ width: 240 }} value={selId} onChange={e => setCid(Number(e.target.value))}>
            {run.candidates.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}
          </select>
        </div>
      )}

      {tab === 'BFS / DFS' && (
        <div className="grid g2">
          <Card title="Breadth-First Search" sub="Queue · level by level · always completes">
            <CriteriaTree node={c.eligibility.bfs.tree} /><div style={{ height: 10 }} /><TraversalTable report={c.eligibility.bfs} />
          </Card>
          <Card title="Depth-First Search" sub="Stack · deep first · stops at the first failed mandatory criterion">
            <CriteriaTree node={c.eligibility.dfs.tree} /><div style={{ height: 10 }} /><TraversalTable report={c.eligibility.dfs} />
          </Card>
        </div>
      )}

      {tab === 'A* Search' && c.eligibility.astar && (
        <>
          <div className="callout">
            <b>A* (informed search)</b> uses a priority queue ordered by <code>f(n) = g(n) + h(n)</code>.&nbsp;
            <b>g(n)</b> = nodes already expanded. &nbsp;<b>h(n)</b> = leaf checks remaining in this subtree (admissible).
            A* visits nodes with the fewest remaining checks first — it reaches individual criteria before expanding large groups.
            Like DFS it stops on the first failure, but unlike DFS its order is guided by the heuristic.
          </div>
          <div className="grid g2">
            <Card title="A* traversal tree" sub={`f(n)=g(n)+h(n) · Visited ${c.eligibility.astar.nodes_visited} of ${c.eligibility.astar.total_nodes} nodes · ${c.eligibility.astar.early_stopped ? `early stop at "${c.eligibility.astar.stopped_at}"` : 'complete'}`}>
              <CriteriaTree node={c.eligibility.astar.tree} />
            </Card>
            <Card title="A* step-by-step" sub="Nodes are expanded in f(n) order — smaller subtrees first">
              <TraversalTable report={c.eligibility.astar} />
              <div style={{ marginTop: 12 }}>
                <b>Algorithm comparison for this candidate:</b>
                <table style={{ marginTop: 8 }}>
                  <thead><tr><th>Algorithm</th><th className="num">Visited</th><th className="num">Early stop</th><th>Eligible</th></tr></thead>
                  <tbody>
                    <tr><td>BFS</td><td className="num">{c.eligibility.bfs.nodes_visited}</td><td className="num">No</td><td><Badge status={c.eligibility.bfs.eligible ? 'pass' : 'fail'} /></td></tr>
                    <tr><td>DFS</td><td className="num">{c.eligibility.dfs.nodes_visited}</td><td className="num">{c.eligibility.dfs.early_stopped ? 'Yes' : 'No'}</td><td><Badge status={c.eligibility.dfs.eligible ? 'pass' : 'fail'} /></td></tr>
                    <tr style={{ background: 'var(--surface-hi)' }}><td><b>A*</b></td><td className="num"><b>{c.eligibility.astar.nodes_visited}</b></td><td className="num">{c.eligibility.astar.early_stopped ? 'Yes' : 'No'}</td><td><Badge status={c.eligibility.astar.eligible ? 'pass' : 'fail'} /></td></tr>
                  </tbody>
                </table>
                {!c.eligibility.agree && <div className="alert err" style={{ marginTop: 8 }}>Algorithms disagreed — check criteria tree.</div>}
              </div>
            </Card>
          </div>
        </>
      )}

      {tab === 'Heuristic' && (
        <Card title="Heuristic best-first search" sub="Eligible candidates sit in a priority queue ordered by h(n). The highest h(n) is expanded first.">
          <table><thead><tr><th>Expansion</th><th>Candidate</th><th className="num">h(n)</th><th className="num">Frontier size</th></tr></thead>
            <tbody>{run.heuristic_best_first.map(s => <tr key={s.step}><td>#{s.step}</td><td><b>{s.name}</b></td><td className="num">{s.h}</td><td className="num">{s.frontier_size}</td></tr>)}</tbody></table>
          {run.heuristic_best_first.length === 0 && <div className="muted">No eligible candidates.</div>}
        </Card>
      )}

      {tab === 'Local Search' && (run.local_search ? (
        <Card title="Hill climbing on the candidate ordering"
          sub={<>Neighbour = {run.local_search.neighbour_definition} Objective = Σ score / log₂(position + 2). Start: <b>{run.local_search.initial_objective}</b> → end: <b>{run.local_search.final_objective}</b></>}>
          <div className="callout">Initial ordering (upload order): {run.local_search.initial_order.map(i => names[i]).join(' → ')}</div>
          {run.local_search.steps.map(s => (
            <div key={s.iteration} className="card" style={{ background: '#fafbfd' }}>
              <b>Iteration {s.iteration}</b> — {s.message}
              <table style={{ marginTop: 8 }}><thead><tr><th>Neighbour (swap)</th><th className="num">Objective</th><th className="num">Gain</th></tr></thead>
                <tbody>{s.neighbours.map((n, i) => (
                  <tr key={i} style={s.chosen && n.swap[0] === s.chosen.swap[0] ? { background: '#f0fdf4' } : undefined}>
                    <td>{n.swapped[0]} ↔ {n.swapped[1]}</td><td className="num">{n.objective}</td>
                    <td className="num" style={{ color: n.gain > 0 ? 'var(--pass)' : 'var(--muted)' }}>{n.gain > 0 ? '+' : ''}{n.gain}</td></tr>))}</tbody></table>
              <div className="small muted" style={{ marginTop: 6 }}>Order after: {s.order.map(i => names[i]).join(' → ')}</div>
            </div>
          ))}
          <div className="callout">Final ordering: <b>{run.local_search.final_order.map(i => names[i]).join(' → ')}</b></div>
        </Card>
      ) : <Card><div className="muted">No eligible candidates.</div></Card>)}

      {tab === 'Simulated Annealing' && (run.simulated_annealing ? (
        <>
          <div className="callout">
            <b>Simulated Annealing</b> escapes local optima by accepting worse solutions with probability&nbsp;
            <code>P = exp(Δ/T)</code>. Temperature <b>T</b> starts at&nbsp;
            <b>{run.simulated_annealing.T0}</b> and cools geometrically (<b>α = {run.simulated_annealing.alpha}</b>).
            At high T the algorithm explores freely; as T → 0 it becomes greedy like hill climbing.
            Unlike HC, SA swaps <em>any</em> two candidates (not just adjacent), giving a larger neighbourhood.
          </div>
          <div className="grid g2">
            <Card title="Convergence" sub={`${run.simulated_annealing.iterations} iterations · ${run.simulated_annealing.accepted_moves} accepted (${run.simulated_annealing.accepted_worse_moves} uphill) · final T = ${run.simulated_annealing.final_temperature}`}>
              <div className="callout">Initial: {run.simulated_annealing.initial_order.map(i => names[i]).join(' → ')}</div>
              <div className="callout">Final:&nbsp;&nbsp; <b>{run.simulated_annealing.final_order.map(i => names[i]).join(' → ')}</b></div>
              <table style={{ marginTop: 8 }}>
                <thead><tr><th>Metric</th><th className="num">Hill Climbing</th><th className="num">Simulated Annealing</th></tr></thead>
                <tbody>
                  <tr><td>Initial objective</td><td className="num">{run.local_search?.initial_objective ?? '—'}</td><td className="num">{run.simulated_annealing.initial_objective}</td></tr>
                  <tr><td>Final objective</td><td className="num">{run.local_search?.final_objective ?? '—'}</td><td className="num">{run.simulated_annealing.final_objective}</td></tr>
                  <tr><td>Neighbour type</td><td>Adjacent swap</td><td>Any-pair swap</td></tr>
                  <tr><td>Accepts worse?</td><td style={{ color: 'var(--fail)' }}>No</td><td style={{ color: 'var(--pass)' }}>Yes (T-controlled)</td></tr>
                </tbody>
              </table>
            </Card>
            <Card title="Selected SA steps" sub="Showing first 15 accepted iterations">
              <table>
                <thead><tr><th>Iter</th><th>Swap</th><th className="num">Δ</th><th className="num">P(accept)</th><th className="num">T</th><th className="num">Best obj</th></tr></thead>
                <tbody>
                  {run.simulated_annealing.steps.filter(s => s.accepted).slice(0, 15).map(s => (
                    <tr key={s.iteration} style={s.worse_accepted ? { background: 'var(--warn-bg, #fffbeb)' } : undefined}>
                      <td>{s.iteration}</td>
                      <td className="small">{s.swapped[0].split(' ')[0]} ↔ {s.swapped[1].split(' ')[0]}</td>
                      <td className="num" style={{ color: s.delta > 0 ? 'var(--pass)' : 'var(--fail)' }}>{s.delta > 0 ? '+' : ''}{s.delta}</td>
                      <td className="num">{s.probability}</td>
                      <td className="num mono">{s.temperature}</td>
                      <td className="num">{s.best_objective}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {run.simulated_annealing.steps.filter(s => s.worse_accepted).length > 0 &&
                <div className="small muted" style={{ marginTop: 6 }}>Highlighted rows = uphill moves accepted (escape from local optima).</div>}
            </Card>
          </div>
        </>
      ) : <Card><div className="muted">No eligible candidates — simulated annealing did not run.</div></Card>)}

      {tab === 'CSP' && (
        <div className="grid g2">
          <Card title="Variables & domains" sub="Each variable's domain holds the candidate's value from the resume">
            <table><thead><tr><th>Variable</th><th>Domain</th></tr></thead>
              <tbody>{Object.entries(c.csp.domains).map(([k, v]) => <tr key={k}><td className="mono">{k}</td><td>{'{' + v.join(', ') + '}'}</td></tr>)}</tbody></table>
          </Card>
          <Card title="Constraints" sub={`Solver: node consistency → backtracking (MRV). Nodes explored: ${c.csp.nodes_explored}`}>
            <table><tbody>{c.csp.constraints.map(k => (
              <tr key={k.name}><td><b>{k.name}</b><div className="small muted">{k.constraint} · {k.hard ? 'hard' : 'soft'}</div></td><td><Badge status={k.status} /></td></tr>))}</tbody></table>
            <h4 style={{ margin: '12px 0 4px' }}>Solver log</h4>
            {c.csp.steps.length ? <ul className="small" style={{ margin: 0, paddingLeft: 18 }}>{c.csp.steps.map((s, i) => <li key={i}>{s}</li>)}</ul> : <div className="small muted">No pruning or backtracking was needed.</div>}
            <div style={{ marginTop: 8 }}><b>Verdict: </b><Badge status={c.csp.valid ? 'valid' : 'fail'} /></div>
          </Card>
        </div>
      )}

      {tab === 'Forward Chaining' && (
        <div className="grid g2">
          <Card title="Inference chain"><ChainView fc={c.forward_chaining} /></Card>
          <Card title="Rule base" sub="Built from the job requirements"><ul className="small" style={{ paddingLeft: 18, margin: 0 }}>{c.forward_chaining.rules.map(r => <li key={r.id}><b>{r.id}</b> {r.text}</li>)}</ul></Card>
        </div>
      )}

      {tab === 'Backward Chaining' && (
        <div className="grid g2">
          <Card title="Goal: is the candidate ELIGIBLE?"><ProofTree node={c.backward_chaining.tree} />
            <div style={{ marginTop: 10 }}><b>Conclusion: </b>{c.backward_chaining.proven ? <Badge status="proven" /> : <Badge status="failed" />}</div>
            {c.backward_chaining.failed_requirements.length > 0 && <div className="alert err" style={{ marginTop: 10 }}>Failed because: {c.backward_chaining.failed_requirements.join('; ')}</div>}
          </Card>
          <Card title="Reasoning log"><pre className="mono" style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{c.backward_chaining.steps.join('\n')}</pre></Card>
        </div>
      )}

      {tab === 'Resolution' && c.resolution && (
        <>
          <div className="callout">
            <b>Resolution Theorem Proving</b> proves eligibility by REFUTATION:
            we add <code>¬eligible</code> to the knowledge base, convert everything to
            CNF clauses, and apply the resolution rule until the <b>empty clause {'{}'}</b> is derived —
            a contradiction that proves the original goal is TRUE.&nbsp;
            Rule: <code>{'{'} A ∨ B {'}'}</code> ∧ <code>{'{'} ¬B ∨ C {'}'}</code> → <code>{'{'} A ∨ C {'}'}</code>
          </div>
          <div className="grid g2">
            <Card title="CNF clause set" sub={`${c.resolution.initial_clauses} initial clauses (${c.resolution.facts_used} facts + ${c.resolution.rules_used} rules + 1 negated goal)`}>
              <table>
                <thead><tr><th>Type</th><th>Clause (CNF)</th><th>Source</th></tr></thead>
                <tbody>{c.resolution.cnf_clauses.map((cl: any, i: number) => (
                  <tr key={i}>
                    <td><span className={`badge ${cl.type === 'fact' ? 'b-pass' : cl.type === 'rule' ? 'b-info' : 'b-fail'}`}>{cl.type}</span></td>
                    <td className="mono small">{'{' + cl.clause.join(' ∨ ') + '}'}</td>
                    <td className="small muted">{cl.source ?? cl.text ?? cl.id ?? ''}</td>
                  </tr>
                ))}</tbody>
              </table>
              {c.resolution.cnf_clauses.length === 30 && <div className="small muted">… (truncated to 30)</div>}
            </Card>
            <Card title="Resolution steps" sub={`${c.resolution.total_clauses - c.resolution.initial_clauses} new clauses derived · Verdict: ${c.resolution.proven ? '✓ PROVEN' : '✗ NOT PROVEN'}`}>
              {c.resolution.resolution_steps.length === 0
                ? <div className="muted">No resolution steps — goal was directly in the fact set or could not be proven.</div>
                : c.resolution.resolution_steps.map((s: any, i: number) => (
                  <div key={i} className="card" style={{ background: s.resolvent.length === 0 ? '#f0fdf4' : '#fafbfd', marginBottom: 6 }}>
                    <div className="small"><b>Resolve</b> <code>{'{' + s.from_clauses[0].join(' ∨ ') + '}'}</code>
                      {' '}with <code>{'{' + s.from_clauses[1].join(' ∨ ') + '}'}</code></div>
                    <div className="small" style={{ marginTop: 4 }}>→ <code className={s.resolvent.length === 0 ? 'pass' : ''}>{s.resolvent.length === 0 ? '{ } EMPTY CLAUSE' : '{' + s.resolvent.join(' ∨ ') + '}'}</code></div>
                    {s.note && <div className="small muted" style={{ marginTop: 2 }}>{s.note}</div>}
                  </div>
                ))}
              <div style={{ marginTop: 10 }}>
                <b>Conclusion: </b><Badge status={c.resolution.proven ? 'proven' : 'failed'} />
                <div className="small muted" style={{ marginTop: 4 }}>{c.resolution.summary}</div>
              </div>
            </Card>
          </div>
        </>
      )}

      {tab === 'Alpha-Beta & Game Tree' && (run.alpha_beta ? (
        <>
          <div className="callout"><b>How to read this.</b> Hiring is not literally a two-player game, so it is modelled as a classic minimax search tree.
            <b> MAX</b> (HR) wants the candidate with the highest value. Each candidate is a <b>MIN</b> node: a skeptical panel scores the candidate under 4 viewpoints
            and the candidate's value is the <i>lowest</i> of them. <b>α</b> = best value MAX is already guaranteed (it starts at the Wait List threshold, {run.alpha_beta.alpha_init}).
            <b> β</b> = best value MIN can force. When β ≤ α, the remaining leaves of that branch cannot change the answer and are <span style={{ color: 'var(--fail)' }}>pruned ✂</span>.
            The search repeats once per opening ({run.job.openings}).</div>
          <div className="row" style={{ marginBottom: 12 }}>
            <span className="badge b-info">Visited {run.alpha_beta.nodes_visited} / {run.alpha_beta.nodes_total} nodes</span>
            <span className="badge b-fail">Pruned {run.alpha_beta.nodes_pruned}</span>
            {run.alpha_beta.rounds.map((r, i) => <button key={i} className={`btn sm ${round === i ? 'primary' : ''}`} onClick={() => setRound(i)}>Round {r.round}</button>)}
          </div>
          {(() => {
            const r = run.alpha_beta!.rounds[Math.min(round, run.alpha_beta!.rounds.length - 1)]
            return (
              <Card title={`Round ${r.round} — ${r.winner_candidate ? `winner: ${names[r.winner_candidate]} (value ${r.value})` : 'no candidate beats the threshold'}`}
                sub={`Visited ${r.nodes_visited} of ${r.nodes_total} nodes · pruned ${r.nodes_pruned} · initial α = ${r.alpha_init}`}>
                <GameTree node={r.tree} winner={r.winner} />
              </Card>
            )
          })()}
        </>
      ) : <Card><div className="muted">No candidates reached the game tree.</div></Card>)}
    </>
  )
}
