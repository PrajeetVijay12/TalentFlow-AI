import { Link, useNavigate } from 'react-router-dom'
import { Icon } from '../components/icons'
import { Avatar, Badge, Card, Kpi, PageHead, ScoreBar, ScoreRing, statusColor } from '../components/ui'
import { useWorkflow } from '../components/workflow'
import { useApp } from '../state'

export default function Dashboard() {
  const { job, candidates, run, running, loadSamples, user } = useApp()
  const nav = useNavigate()
  const wf = useWorkflow()

  const s = run?.summary
  const firstName = user?.name.split(' ')[0] ?? 'there'

  return (
    <>
      {/* ---- Welcome / action banner ---- */}
      <div className="action-banner">
        <div>
          <div className="ab-label">HR Dashboard</div>
          <h2>
            {!wf.hasResumes
              ? `Welcome, ${firstName} — let's find your next hire`
              : !wf.hasRun
                ? `${candidates.length} application${candidates.length !== 1 ? 's' : ''} ready to screen`
                : `Screening complete — ${s?.Selected ?? 0} candidate${(s?.Selected ?? 0) !== 1 ? 's' : ''} shortlisted`}
          </h2>
          <p>
            {!wf.hasResumes
              ? 'Upload candidate resumes or load the 7 sample profiles to see AI screening in action.'
              : !wf.hasRun
                ? `The AI pipeline will check eligibility, score and rank every applicant for "${job?.title ?? 'the role'}".`
                : `${s?.Rejected ?? 0} rejected · ${s?.['Wait List'] ?? 0} on wait list. Open any candidate to see the full AI reasoning.`}
          </p>
        </div>
        <div className="row">
          {!wf.hasResumes && (
            <>
              <button className="btn btn-white" onClick={loadSamples}>Load sample data</button>
              <Link className="btn btn-white-solid lg" to="/upload">
                <Icon name="upload" /> Upload Resumes
              </Link>
            </>
          )}
          {wf.hasResumes && !wf.hasRun && (
            <button className="btn btn-white-solid lg" disabled={running}
              onClick={() => nav('/pipeline', { state: { autorun: true } })}>
              <Icon name="play" /> Start AI Screening
            </button>
          )}
          {wf.hasRun && (
            <Link className="btn btn-white-solid lg" to="/ranking">
              <Icon name="trophy" /> View Shortlist
            </Link>
          )}
        </div>
      </div>

      {/* ---- Hiring funnel (only after run) ---- */}
      {run && s ? (
        <>
          <div className="hire-funnel">
            <div className="hf-stage hf-total">
              <div className="hf-label">Total Applied</div>
              <div className="hf-val">{s.total}</div>
              <div className="hf-sub">Resumes submitted</div>
            </div>
            <div className="hf-stage hf-eligible">
              <div className="hf-label">Passed Eligibility</div>
              <div className="hf-val">{s.eligible}</div>
              <div className="hf-sub">{s.total > 0 ? Math.round((s.eligible / s.total) * 100) : 0}% of applicants</div>
            </div>
            <div className="hf-stage hf-selected">
              <div className="hf-label">Shortlisted</div>
              <div className="hf-val">{s.Selected}</div>
              <div className="hf-sub">{s['Wait List']} on wait list</div>
            </div>
            <div className="hf-stage hf-rejected">
              <div className="hf-label">Rejected</div>
              <div className="hf-val">{s.Rejected}</div>
              <div className="hf-sub">Did not meet criteria</div>
            </div>
          </div>

          {/* Top shortlisted candidates */}
          {run.ranking.filter(r => r.status === 'Selected').length > 0 && (
            <Card title="Top Shortlisted Candidates" icon="trophy"
              right={<Link to="/ranking" className="small">View all →</Link>}
              sub="AI-ranked candidates recommended for interview">
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Rank</th>
                      <th>Candidate</th>
                      <th>Degree · CGPA · Experience</th>
                      <th className="num">AI Score</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {run.ranking.slice(0, 5).map(r => {
                      const c = run.candidates.find(x => x.id === r.id)!
                      return (
                        <tr key={r.id} className="click" onClick={() => nav(`/candidates/${r.id}`)}>
                          <td><span className={`rank-no ${r.status === 'Selected' && r.rank <= 3 ? `r${r.rank}` : ''}`}>{r.rank}</span></td>
                          <td>
                            <div className="cell-person">
                              <Avatar name={r.name} />
                              <div>
                                <b>{r.name}</b>
                                <div className="small muted">{c.profile.email ?? ''}</div>
                              </div>
                            </div>
                          </td>
                          <td className="muted" style={{ fontSize: 13 }}>
                            {c.profile.degree ?? '—'} · {c.profile.cgpa ?? '—'} · {c.profile.experience} yr
                          </td>
                          <td className="num"><ScoreBar value={r.score} color={statusColor(r.status)} /></td>
                          <td><Badge status={r.status} /></td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
        </>
      ) : (
        /* ---- Before run: role + queue cards ---- */
        <div className="grid g2">
          <Card title="Active Role" icon="job" right={<Link to="/job" className="small">Edit →</Link>}
            sub="Requirements the AI will screen every applicant against">
            {job ? (
              <table><tbody>
                <tr><td className="muted">Role title</td><td><b>{job.title}</b></td></tr>
                <tr><td className="muted">Required degree</td><td>{job.required_degrees.join(' / ') || 'Any'}</td></tr>
                <tr><td className="muted">Min CGPA</td><td>≥ {job.min_cgpa}</td></tr>
                <tr><td className="muted">Min experience</td><td>≥ {job.min_experience} years</td></tr>
                <tr><td className="muted">Required skills</td><td>{job.required_skills.map(x => <span key={x} className="chip">{x}</span>)}</td></tr>
                <tr><td className="muted">Certifications</td><td>{job.required_certifications.map(x => <span key={x} className="chip">{x}</span>)}{job.required_certifications.length === 0 && <span className="muted">None required</span>}</td></tr>
                <tr><td className="muted">Location · Openings</td><td>{job.location ?? 'Any'} · {job.openings} opening{job.openings !== 1 ? 's' : ''}</td></tr>
              </tbody></table>
            ) : <span className="muted">Loading…</span>}
          </Card>

          <Card title="Application Queue" icon="file"
            sub={candidates.length > 0 ? `${candidates.length} resume${candidates.length !== 1 ? 's' : ''} parsed and ready` : 'No resumes uploaded yet'}>
            {candidates.length > 0 ? (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
                  {candidates.slice(0, 5).map(c => (
                    <div key={c.id} className="cell-person">
                      <Avatar name={c.name} />
                      <div>
                        <b style={{ fontSize: 13.5 }}>{c.name}</b>
                        <div className="small muted">{c.degree ?? '—'} · {c.experience} yr · {c.location ?? '—'}</div>
                      </div>
                    </div>
                  ))}
                  {candidates.length > 5 && <div className="small muted">+{candidates.length - 5} more applicants</div>}
                </div>
                <button className="btn primary lg" style={{ width: '100%' }} disabled={running}
                  onClick={() => nav('/pipeline', { state: { autorun: true } })}>
                  <Icon name="play" /> Run AI Screening
                </button>
              </>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <p className="muted" style={{ margin: 0 }}>
                  Upload candidate resumes to begin. The AI will parse, score and rank them automatically.
                </p>
                <div className="row">
                  <button className="btn" onClick={loadSamples}>Load 7 sample resumes</button>
                  <Link className="btn primary" to="/upload"><Icon name="upload" /> Upload</Link>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* ---- How the screening works ---- */}
      {!wf.hasRun && (
        <div style={{ marginTop: 16 }}>
        <Card title="How AI Screening Works" icon="list" sub="Four steps from upload to shortlist">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 14, marginTop: 4 }}>
            {[
              { no: '1', title: 'Upload Applications', desc: 'PDF/DOCX resumes are parsed into structured candidate profiles automatically.' },
              { no: '2', title: 'Set Job Brief', desc: 'Define degree, CGPA, experience, skills and location requirements for the role.' },
              { no: '3', title: 'AI Screening', desc: 'Eligibility check → scoring → ranking → constraint validation → reasoning.' },
              { no: '4', title: 'Review & Decide', desc: 'Read each candidate\'s AI decision with a plain-English explanation and export.' },
            ].map(step => (
              <div key={step.no} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <div style={{ width: 32, height: 32, borderRadius: 8, background: 'var(--accent)', color: '#fff', display: 'grid', placeItems: 'center', fontWeight: 700, flexShrink: 0 }}>{step.no}</div>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: 4, fontSize: 13.5 }}>{step.title}</div>
                  <div style={{ color: 'var(--muted)', fontSize: 12.5, lineHeight: 1.55 }}>{step.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </Card>
        </div>
      )}
    </>
  )
}
