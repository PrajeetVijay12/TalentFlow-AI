import { Link, useParams } from 'react-router-dom'
import { Avatar, Badge, Card, NeedRun, PageHead, ScoreRing, statusColor } from '../components/ui'
import { CriteriaTree, GameTree, ProofTree, TraversalTable } from '../components/trees'
import { ChainView } from '../components/chain'
import { useApp } from '../state'
import { downloadReport } from '../utils/reportGenerator'

export default function CandidateDetail() {
  const { id } = useParams()
  const { run } = useApp()
  if (!run) return <><PageHead title="Candidate Details" /><NeedRun what="candidate details" /></>
  const c = run.candidates.find(x => String(x.id) === id)
  if (!c) return <><PageHead title="Candidate not found" /><Link to="/results">← Back to results</Link></>

  const p = c.profile
  const h = c.heuristic
  const myRound = run.alpha_beta?.rounds.find(r => r.tree.children.some(n => n.id === `c${c.id}`))

  return (
    <>
      <div className="row" style={{ marginBottom: 14, gap: 8 }}>
        <Link className="btn sm" to="/results">← All candidates</Link>
        <button className="btn sm" onClick={() => downloadReport(c, run.job)}>Download Report</button>
      </div>
      <div className="card" style={{ marginBottom: 16 }}>
        <div className="cand-hero">
          <Avatar name={c.name} large />
          <div className="who">
            <div className="row"><h1>{c.name}</h1><Badge status={c.final.status} /></div>
            <div className="links">{p.email ?? 'no email'} · {p.phone ?? 'no phone'} · <span className="mono">{p.filename}</span></div>
            <div className="links">Rank <b style={{ color: 'var(--ink)' }}>#{c.final.rank}</b> of {run.ranking.length} · {p.degree ?? '—'} · CGPA {p.cgpa ?? '—'} · {p.experience} yr</div>
          </div>
          <ScoreRing value={c.final.score} size={128} color={statusColor(c.final.status)} label="h-score" />
        </div>
      </div>

      <div className="grid g2">
        <Card title="Why this decision?" icon="list" sub="Plain-language explanation generated from the pipeline results">
          <ul style={{ margin: 0, paddingLeft: 18 }}>{c.final.reasons.map((r, i) => <li key={i} style={{ marginBottom: 4 }}>{r}</li>)}</ul>
        </Card>
        <Card title="Pipeline verdicts" icon="pipeline">
          <table><tbody>
            <tr><td>BFS / DFS eligibility</td><td><Badge status={c.eligibility.eligible ? 'pass' : 'fail'} /></td></tr>
            <tr><td>CSP hard constraints</td><td><Badge status={c.csp.valid ? 'pass' : 'fail'} /></td></tr>
            <tr><td>Forward chaining</td><td><Badge status={c.forward_chaining.goal_reached ? 'pass' : 'fail'} /> <span className="small muted">eligible = {String(c.forward_chaining.goal_reached).toUpperCase()}</span></td></tr>
            <tr><td>Backward chaining</td><td><Badge status={c.backward_chaining.proven ? 'proven' : 'failed'} /></td></tr>
            <tr><td>Alpha-Beta</td><td className="small">{c.alpha_beta.status}</td></tr>
          </tbody></table>
        </Card>
      </div>

      <div style={{ height: 16 }} />
      <div className="grid g2">
        <Card title="Extracted resume data" icon="file" sub="Structured data produced by the rule-based parser">
          <table><tbody>
            <tr><td className="muted">Degree · CGPA</td><td>{p.degree ?? '—'} · {p.cgpa ?? '—'}</td></tr>
            <tr><td className="muted">Experience</td><td>{p.experience} years</td></tr>
            <tr><td className="muted">Location</td><td>{p.location ?? '—'}</td></tr>
            <tr><td className="muted">Skills</td><td>{p.skills.map(s => <span key={s} className="chip">{s}</span>)}</td></tr>
            <tr><td className="muted">Projects</td><td>{p.projects.map(x => <div key={x.name}>{x.name} <span className="badge b-info">{x.score}</span> <span className="small muted">({x.evidence})</span></div>)}{p.projects.length === 0 && '—'}</td></tr>
            <tr><td className="muted">Certifications</td><td>{p.certifications.map(s => <span key={s} className="chip">{s}</span>)}{p.certifications.length === 0 && '—'}</td></tr>
          </tbody></table>
          <div className="small muted" style={{ marginTop: 8 }}><b>Extraction notes:</b> {p.notes.join(' ') || '—'}</div>
        </Card>

        <Card title="Heuristic score breakdown" icon="target" sub={h ? <span className="mono">{h.formula} = {h.total}</span> : 'Not scored — candidate failed eligibility, so expensive stages were skipped.'}>
          {h ? (
            <table><thead><tr><th>Component</th><th className="num">Score</th><th className="num">Weight</th><th className="num">Contribution</th></tr></thead>
              <tbody>
                <tr><td>Skills<div className="small muted">{h.parts.skills.matched.length}/{h.parts.skills.required} matched
                  {h.parts.skills.missing.map(m => <span key={m} className="chip miss">{m}</span>)}</div></td>
                  <td className="num">{h.parts.skills.score}</td><td className="num">{(h.parts.skills.weight * 100).toFixed(0)}%</td><td className="num"><b>{h.parts.skills.weighted}</b></td></tr>
                <tr><td>Experience<div className="small muted">{h.parts.experience.candidate} / {h.parts.experience.required} yr (capped at 100)</div></td>
                  <td className="num">{h.parts.experience.score}</td><td className="num">{(h.parts.experience.weight * 100).toFixed(0)}%</td><td className="num"><b>{h.parts.experience.weighted}</b></td></tr>
                <tr><td>Projects<div className="small muted">{h.parts.projects.best_project ?? 'no projects'} {h.parts.projects.category && `(${h.parts.projects.category.replace('_', ' ')})`}</div></td>
                  <td className="num">{h.parts.projects.score}</td><td className="num">{(h.parts.projects.weight * 100).toFixed(0)}%</td><td className="num"><b>{h.parts.projects.weighted}</b></td></tr>
                <tr><td>Certifications<div className="small muted">{h.parts.certifications.matched.length}/{h.parts.certifications.required} matched
                  {h.parts.certifications.missing.map(m => <span key={m} className="chip miss">{m}</span>)}</div></td>
                  <td className="num">{h.parts.certifications.score}</td><td className="num">{(h.parts.certifications.weight * 100).toFixed(0)}%</td><td className="num"><b>{h.parts.certifications.weighted}</b></td></tr>
                <tr><td colSpan={3}><b>Final score</b></td><td className="num"><b>{h.total}</b></td></tr>
              </tbody></table>
          ) : <div className="muted">—</div>}
          {c.local_search && <div className="callout" style={{ marginTop: 12 }}>
            <b>Local search:</b> {c.local_search.moved ? `moved from position ${c.local_search.initial_rank} (upload order) to ${c.local_search.final_rank}.` : `stayed at position ${c.local_search.final_rank}.`}
          </div>}
        </Card>
      </div>

      <div style={{ height: 16 }} />
      <Card title="Eligibility — BFS vs DFS" icon="git" sub="Both traverse the same criteria tree; they differ in order and in early termination.">
        <div className="grid g2">
          <div><h4 style={{ marginBottom: 6 }}>Result tree</h4><CriteriaTree node={c.eligibility.bfs.tree} />
            <div style={{ marginTop: 8 }}><b>Final: </b><Badge status={c.eligibility.eligible ? 'eligible' : 'fail'} /></div></div>
          <div className="small">
            <h4 style={{ marginBottom: 6 }}>Check summary</h4>
            <table><tbody>{c.eligibility.bfs.checks.map(k => (
              <tr key={k.id}><td><b>{k.label}</b><div className="muted">required {k.required} · candidate {k.actual}</div></td><td><Badge status={k.status} /></td></tr>))}</tbody></table>
          </div>
        </div>
        <details style={{ marginTop: 12 }}><summary><b>BFS traversal</b> ({c.eligibility.bfs.nodes_visited} nodes)</summary><TraversalTable report={c.eligibility.bfs} /></details>
        <details style={{ marginTop: 8 }}><summary><b>DFS traversal</b> ({c.eligibility.dfs.nodes_visited} nodes{c.eligibility.dfs.early_stopped ? ', stopped early' : ''})</summary><TraversalTable report={c.eligibility.dfs} /></details>
      </Card>

      <div style={{ height: 16 }} />
      <div className="grid g2">
        <Card title="Constraint satisfaction (CSP)" icon="shield" sub={`${c.csp.variables} variables · ${c.csp.nodes_explored} backtracking nodes explored`}>
          <table><thead><tr><th>Constraint</th><th>Candidate</th><th>Type</th><th>Result</th></tr></thead>
            <tbody>{c.csp.constraints.map(k => (
              <tr key={k.name}><td><b>{k.name}</b><div className="small muted">{k.constraint}</div></td><td>{k.candidate_value}</td>
                <td className="small">{k.hard ? 'hard' : 'soft'}</td><td><Badge status={k.status} /></td></tr>))}</tbody></table>
          <div style={{ marginTop: 8 }}><b>CSP verdict: </b><Badge status={c.csp.valid ? 'valid' : 'fail'} />{!c.csp.valid && <span className="small muted"> violated: {c.csp.failed_hard.join(', ')}</span>}</div>
        </Card>
        <Card title="Forward chaining" icon="list" sub="Data-driven: facts → rules → new facts">
          <ChainView fc={c.forward_chaining} />
        </Card>
      </div>

      <div style={{ height: 16 }} />
      <div className="grid g2">
        <Card title="Backward chaining" icon="git" sub="Goal-driven: “Is the candidate eligible?” → what must be true?">
          <ProofTree node={c.backward_chaining.tree} />
          <div style={{ marginTop: 8 }}><b>Conclusion: </b>{c.backward_chaining.proven ? <Badge status="proven" /> : <><Badge status="failed" /> <span className="small muted">missing: {c.backward_chaining.failed_requirements.join('; ')}</span></>}</div>
        </Card>
        <Card title="Alpha-Beta pruning" icon="trophy" sub={c.alpha_beta.status}>
          {c.perspectives ? (<>
            <table><thead><tr><th>Panel viewpoint (leaf)</th><th className="num">Score</th></tr></thead>
              <tbody>{c.perspectives.map(x => <tr key={x.id}><td>{x.label}</td><td className="num">{x.score}</td></tr>)}</tbody></table>
            <div className="small muted" style={{ marginTop: 8 }}>The candidate’s MIN value is the lowest of these (its worst case). MAX (HR) prefers the highest worst case.</div>
            {myRound && <div style={{ marginTop: 10 }}><GameTree node={myRound.tree.children.find(n => n.id === `c${c.id}`)!} /></div>}
          </>) : <div className="muted">Not in the game tree — eliminated by an earlier stage.</div>}
        </Card>
      </div>
    </>
  )
}
