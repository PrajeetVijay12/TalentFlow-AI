import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api'
import { Avatar, Badge, PageHead, ScoreBar, ScoreRing, statusColor } from '../components/ui'
import { Icon } from '../components/icons'
import type { HistoryDetail, HistoryEntry } from '../types'

function fmt(d: string) {
  return new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

function DetailModal({ id, onClose }: { id: number; onClose: () => void }) {
  const [data, setData] = useState<HistoryDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('All')
  const nav = useNavigate()

  useEffect(() => {
    api.getHistoryDetail(id).then(d => { setData(d); setLoading(false) }).catch(() => setLoading(false))
  }, [id])

  if (loading) return (
    <div className="hd-overlay" onClick={onClose}>
      <div className="hd-modal" onClick={e => e.stopPropagation()}>
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--muted)' }}>Loading…</div>
      </div>
    </div>
  )
  if (!data?.run) return (
    <div className="hd-overlay" onClick={onClose}>
      <div className="hd-modal" onClick={e => e.stopPropagation()}>
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--muted)' }}>No results saved for this recruitment.</div>
      </div>
    </div>
  )

  const run = data.run
  const s = run.summary
  const counts: Record<string, number> = { All: run.candidates.length, Selected: s.Selected, 'Wait List': s['Wait List'], Rejected: s.Rejected }
  const rows = [...run.candidates].sort((a, b) => a.final.rank - b.final.rank).filter(c => filter === 'All' || c.final.status === filter)

  return (
    <div className="hd-overlay" onClick={onClose}>
      <div className="hd-modal" onClick={e => e.stopPropagation()}>
        {/* Modal header */}
        <div className="hd-modal-head">
          <div>
            <div className="eyebrow">{fmt(data.created)}</div>
            <h2 style={{ margin: 0, fontSize: 20 }}>{data.name}</h2>
            <div style={{ color: 'var(--muted)', fontSize: 13, marginTop: 3 }}>
              {data.job.title} · {data.job.location ?? 'Any location'} · {data.candidates_count} applicants
            </div>
          </div>
          <button className="btn sm" onClick={onClose}><Icon name="x" /> Close</button>
        </div>

        {/* Funnel */}
        <div className="hire-funnel" style={{ margin: '16px 0' }}>
          <div className="hf-stage hf-total"><div className="hf-label">Total</div><div className="hf-val">{s.total}</div></div>
          <div className="hf-stage hf-eligible"><div className="hf-label">Eligible</div><div className="hf-val">{s.eligible}</div></div>
          <div className="hf-stage hf-selected"><div className="hf-label">Shortlisted</div><div className="hf-val">{s.Selected}</div></div>
          <div className="hf-stage hf-rejected"><div className="hf-label">Rejected</div><div className="hf-val">{s.Rejected}</div></div>
        </div>

        {/* Filter tabs */}
        <div className="tabs" style={{ marginBottom: 16 }}>
          {(['All', 'Selected', 'Wait List', 'Rejected'] as const).map(f => (
            <button key={f} className={filter === f ? 'on' : ''} onClick={() => setFilter(f)}>
              {f} <span style={{ opacity: .65 }}>({counts[f]})</span>
            </button>
          ))}
        </div>

        {/* Candidate cards */}
        <div className="cand-grid">
          {rows.map(c => {
            const status = c.final.status
            const ccCls = status === 'Selected' ? 'cc-selected' : status === 'Wait List' ? 'cc-wait' : 'cc-rejected'
            const icon = status === 'Selected' ? '✅' : status === 'Wait List' ? '⏳' : '❌'
            return (
              <div key={c.id} className={`cand-card ${ccCls}`}
                style={{ cursor: 'default' }}>
                <div className="cc-header">
                  <Avatar name={c.name} />
                  <div className="cc-name">
                    <h3>{c.name}</h3>
                    <div className="cc-meta">{c.profile.degree ?? '—'} · {c.profile.location ?? '—'}</div>
                  </div>
                  <Badge status={status} />
                </div>
                <div className="cc-score-row">
                  <ScoreRing value={c.final.score} size={56} color={statusColor(status)} label="" />
                  <div className="cc-score-details">
                    <div className="csd-row"><span className="csd-label">Score</span><span className="csd-val" style={{ color: statusColor(status) }}>{c.final.score !== null ? Number(c.final.score.toFixed(1)) : '—'}</span></div>
                    <div className="csd-row"><span className="csd-label">Exp</span><span className="csd-val">{c.profile.experience} yr</span></div>
                    <div className="csd-row"><span className="csd-label">CGPA</span><span className="csd-val">{c.profile.cgpa ?? '—'}</span></div>
                  </div>
                  <div style={{ textAlign: 'right', alignSelf: 'flex-start' }}>
                    <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.06em', fontWeight: 600 }}>Rank</div>
                    <div style={{ fontSize: 22, fontWeight: 700, lineHeight: 1.1 }}>#{c.final.rank}</div>
                  </div>
                </div>
                <div className={`cc-decision ${ccCls}`}>
                  <span className="cd-icon">{icon}</span>
                  <span>{c.final.reasons[0] ?? '—'}</span>
                </div>
                {c.profile.skills.length > 0 && (
                  <div className="cc-skills">
                    {c.profile.skills.slice(0, 5).map(s => <span key={s} className="chip">{s}</span>)}
                    {c.profile.skills.length > 5 && <span className="chip">+{c.profile.skills.length - 5}</span>}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default function HistoryPage() {
  const [entries, setEntries] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<number | null>(null)
  const [deleting, setDeleting] = useState<number | null>(null)
  const nav = useNavigate()

  const load = () => {
    setLoading(true)
    api.history().then(d => { setEntries(d); setLoading(false) }).catch(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  async function handleDelete(id: number) {
    setDeleting(id)
    try { await api.deleteHistory(id); setEntries(e => e.filter(x => x.id !== id)) }
    catch { /* ignore */ }
    finally { setDeleting(null) }
  }

  async function handleReopen(id: number) {
    try {
      await api.reopenHistory(id)
      nav('/upload')
      window.location.reload()
    } catch { /* ignore */ }
  }

  return (
    <>
      <PageHead
        title="Recruitment History"
        desc="All past AI screening sessions. Click 'View Results' to see the full candidate breakdown."
      />

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: 48, color: 'var(--muted)' }}>Loading history…</div>
      ) : entries.length === 0 ? (
        <div className="card empty">
          <div className="big-ico"><Icon name="file" /></div>
          <h3>No past recruitments yet</h3>
          <p>Complete your first AI screening and it will appear here automatically.</p>
          <div className="row" style={{ justifyContent: 'center', marginTop: 8 }}>
            <button className="btn primary" onClick={() => nav('/wizard')}>
              <Icon name="play" /> Start New Recruitment
            </button>
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {entries.map(e => (
            <div key={e.id} className="hist-card card">
              <div className="hist-card-left">
                <div className="hist-icon">
                  <Icon name="users" />
                </div>
                <div className="hist-info">
                  <div className="hist-name">{e.name}</div>
                  <div className="hist-meta">
                    <span>{e.title}</span>
                    {e.location && <><span className="hist-dot">·</span><span>{e.location}</span></>}
                    <span className="hist-dot">·</span>
                    <span>{e.openings} opening{e.openings !== 1 ? 's' : ''}</span>
                    <span className="hist-dot">·</span>
                    <span>{fmt(e.created)}</span>
                  </div>
                  <div className="hist-stats">
                    <span className="hist-stat">
                      <span className="hs-num">{e.candidates_count}</span> applicants
                    </span>
                  </div>
                </div>
              </div>
              <div className="hist-card-right">
                <button className="btn sm" onClick={() => handleReopen(e.id)}>
                  <Icon name="upload" /> Reuse Criteria
                </button>
                <button className="btn sm primary" onClick={() => setSelected(e.id)}>
                  View Results
                </button>
                <button className="btn sm danger" disabled={deleting === e.id}
                  onClick={() => handleDelete(e.id)}>
                  {deleting === e.id ? '…' : <Icon name="x" />}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {selected !== null && (
        <DetailModal id={selected} onClose={() => setSelected(null)} />
      )}
    </>
  )
}
