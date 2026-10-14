import { Link } from 'react-router-dom'
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Avatar, Badge, Card, NeedRun, PageHead, ScoreBar, ScoreRing, fmt, statusColor } from '../components/ui'
import { useApp } from '../state'

export default function RankingPage() {
  const { run } = useApp()
  if (!run) return <><PageHead title="Shortlist" /><NeedRun what="the shortlist" /></>

  const th = run.job.thresholds
  const chart = run.ranking.filter(r => r.score !== null).map(r => ({
    name: r.name.split(' ')[0], score: r.score as number, status: r.status,
  }))
  const selected = run.ranking.filter(r => r.status === 'Selected')
  const waitList = run.ranking.filter(r => r.status === 'Wait List')

  function exportCsv() {
    const rows = [
      ['Rank', 'Candidate', 'Score', 'Status', 'Decision'],
      ...run!.ranking.map(r => {
        const c = run!.candidates.find(x => x.id === r.id)!
        return [r.rank, r.name, r.score ?? '', r.status, `"${c.final.reasons[0] ?? ''}"`]
      }),
    ]
    const blob = new Blob([rows.map(r => r.join(',')).join('\n')], { type: 'text/csv' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob); a.download = 'shortlist.csv'; a.click()
  }

  return (
    <>
      <PageHead
        eyebrow="Step 4 of 4 · Final Decision"
        title="Shortlist"
        desc={`AI screening for "${run.job.title}" — ${selected.length} shortlisted, ${waitList.length} on wait list.`}
        actions={<button className="btn" onClick={exportCsv}>Export CSV</button>}
      />

      {/* ---- Selected: featured profile cards ---- */}
      {selected.length > 0 && (
        <>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div>
              <h2 style={{ fontSize: 17, fontWeight: 700, marginBottom: 2 }}>Shortlisted for Interview</h2>
              <p style={{ margin: 0, color: 'var(--muted)', fontSize: 13 }}>
                These candidates met all requirements and scored ≥ {th.selected}
              </p>
            </div>
            <Badge status="Selected" />
          </div>
          <div className="shortlist-grid">
            {selected.map(p => {
              const c = run.candidates.find(x => x.id === p.id)!
              return (
                <Link key={p.id} to={`/candidates/${p.id}`} className="shortlist-card">
                  <div className="sc-rank">#{p.rank}</div>
                  <ScoreRing value={p.score} size={80} color={statusColor(p.status)} label="score" />
                  <div className="sc-name">{p.name}</div>
                  <div className="sc-detail">
                    {c.profile.degree ?? '—'}<br />
                    CGPA {c.profile.cgpa ?? '—'} · {c.profile.experience} yr exp
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, justifyContent: 'center' }}>
                    {c.profile.skills.slice(0, 3).map(s => <span key={s} className="chip">{s}</span>)}
                  </div>
                  <div className="sc-badge"><Badge status="Selected" /></div>
                </Link>
              )
            })}
          </div>
        </>
      )}

      {/* ---- Wait list ---- */}
      {waitList.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Wait List</h2>
            <Badge status="Wait List" />
            <span style={{ color: 'var(--muted)', fontSize: 13 }}>Score ≥ {th.waitlist}, below {th.selected}</span>
          </div>
          <Card>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Rank</th><th>Candidate</th><th>Degree · CGPA · Exp</th><th className="num">Score</th><th>Decision</th></tr></thead>
                <tbody>
                  {waitList.map(r => {
                    const c = run.candidates.find(x => x.id === r.id)!
                    return (
                      <tr key={r.id}>
                        <td><span className="rank-no">{r.rank}</span></td>
                        <td><Link to={`/candidates/${r.id}`}><div className="cell-person"><Avatar name={r.name} /><b>{r.name}</b></div></Link></td>
                        <td className="small muted">{c.profile.degree ?? '—'} · {c.profile.cgpa ?? '—'} · {c.profile.experience} yr</td>
                        <td className="num"><ScoreBar value={r.score} color={statusColor(r.status)} /></td>
                        <td className="small muted" style={{ maxWidth: 280 }}>{c.final.reasons[0]}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* ---- Full ranked table + chart ---- */}
      <div className="split">
        <Card title="Full Ranking" icon="trophy" sub="All candidates ordered by AI score">
          <div className="table-wrap">
            <table>
              <thead><tr><th>Rank</th><th>Candidate</th><th className="num">AI Score</th><th>Outcome</th><th>Decision Reason</th></tr></thead>
              <tbody>
                {run.ranking.map(r => {
                  const c = run.candidates.find(x => x.id === r.id)!
                  return (
                    <tr key={r.id}>
                      <td><span className={`rank-no ${r.status === 'Selected' && r.rank <= 3 ? `r${r.rank}` : ''}`}>{r.rank}</span></td>
                      <td>
                        <Link to={`/candidates/${r.id}`}>
                          <div className="cell-person"><Avatar name={r.name} /><b>{r.name}</b></div>
                        </Link>
                      </td>
                      <td className="num"><ScoreBar value={r.score} color={statusColor(r.status)} /></td>
                      <td><Badge status={r.status} /></td>
                      <td className="small muted" style={{ minWidth: 200 }}>{c.final.reasons[0]}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>

        <Card title="Score Distribution" icon="target"
          sub={`Dashed lines: shortlist ≥ ${th.selected}, wait list ≥ ${th.waitlist}`}>
          <ResponsiveContainer width="100%" height={Math.max(200, chart.length * 52)}>
            <BarChart data={chart} layout="vertical" margin={{ left: 0, right: 18 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tickLine={false} axisLine={false} />
              <YAxis type="category" dataKey="name" width={68} tickLine={false} axisLine={false} />
              <Tooltip cursor={{ fill: 'rgba(124,58,237,.06)' }} />
              <ReferenceLine x={th.selected} stroke="var(--pass)" strokeDasharray="4 4"
                label={{ value: `${th.selected}`, fill: 'var(--pass)', fontSize: 11, position: 'top' }} />
              <ReferenceLine x={th.waitlist} stroke="var(--warn)" strokeDasharray="4 4"
                label={{ value: `${th.waitlist}`, fill: 'var(--warn)', fontSize: 11, position: 'top' }} />
              <Bar dataKey="score" radius={[0, 8, 8, 0]} barSize={20} isAnimationActive={false}>
                {chart.map((c, i) => <Cell key={i} fill={statusColor(c.status)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="small muted" style={{ marginTop: 8 }}>
            {fmt(run.ranking.length - chart.length, 0)} ineligible candidate{run.ranking.length - chart.length !== 1 ? 's' : ''} not scored.
          </div>
          <div className="legend-row" style={{ marginTop: 10 }}>
            <span><i style={{ background: 'var(--pass)', display: 'inline-block', width: 10, height: 10, borderRadius: 3, marginRight: 5 }} />Shortlisted</span>
            <span><i style={{ background: 'var(--warn)', display: 'inline-block', width: 10, height: 10, borderRadius: 3, marginRight: 5 }} />Wait List</span>
            <span><i style={{ background: 'var(--fail)', display: 'inline-block', width: 10, height: 10, borderRadius: 3, marginRight: 5 }} />Rejected</span>
          </div>
        </Card>
      </div>
    </>
  )
}
