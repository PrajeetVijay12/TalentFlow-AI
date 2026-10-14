import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Avatar, Badge, NeedRun, PageHead, ScoreRing, statusColor } from '../components/ui'
import { useApp } from '../state'
import type { CandidateResult } from '../types'

function CandCard({ c }: { c: CandidateResult }) {
  const nav = useNavigate()
  const status = c.final.status
  const ccCls = status === 'Selected' ? 'cc-selected' : status === 'Wait List' ? 'cc-wait' : 'cc-rejected'
  const icon = status === 'Selected' ? '✅' : status === 'Wait List' ? '⏳' : '❌'

  return (
    <div className={`cand-card ${ccCls}`} onClick={() => nav(`/candidates/${c.id}`)}>
      {/* Header: avatar + name + badge */}
      <div className="cc-header">
        <Avatar name={c.name} />
        <div className="cc-name">
          <h3>{c.name}</h3>
          <div className="cc-meta">
            {c.profile.degree ?? '—'} &nbsp;·&nbsp; {c.profile.location ?? '—'}
          </div>
        </div>
        <Badge status={status} />
      </div>

      {/* Score row */}
      <div className="cc-score-row">
        <ScoreRing value={c.final.score} size={60} color={statusColor(status)} label="score" />
        <div className="cc-score-details">
          <div className="csd-row">
            <span className="csd-label">AI Score</span>
            <span className="csd-val" style={{ color: statusColor(status) }}>
              {c.final.score !== null ? Number(c.final.score.toFixed(1)) : '—'} / 100
            </span>
          </div>
          <div className="csd-row">
            <span className="csd-label">Experience</span>
            <span className="csd-val">{c.profile.experience} yr</span>
          </div>
          <div className="csd-row">
            <span className="csd-label">CGPA</span>
            <span className="csd-val">{c.profile.cgpa ?? '—'}</span>
          </div>
          <div className="csd-row">
            <span className="csd-label">Eligibility</span>
            <span>
              {c.eligibility.eligible
                ? <span style={{ color: 'var(--pass)', fontSize: 12, fontWeight: 600 }}>✓ Passed</span>
                : <span style={{ color: 'var(--fail)', fontSize: 12, fontWeight: 600 }}>✗ Failed</span>}
            </span>
          </div>
        </div>
        <div style={{ textAlign: 'right', alignSelf: 'flex-start' }}>
          <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.06em', fontWeight: 600 }}>Rank</div>
          <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-.02em', lineHeight: 1.1 }}>#{c.final.rank}</div>
        </div>
      </div>

      {/* AI Decision */}
      <div className={`cc-decision ${ccCls}`}>
        <span className="cd-icon">{icon}</span>
        <span>{c.final.reasons[0] ?? 'No reason provided.'}</span>
      </div>

      {/* Skills */}
      {c.profile.skills.length > 0 && (
        <div className="cc-skills">
          {c.profile.skills.slice(0, 6).map(s => <span key={s} className="chip">{s}</span>)}
          {c.profile.skills.length > 6 && <span className="chip">+{c.profile.skills.length - 6} more</span>}
        </div>
      )}

      {/* Footer */}
      <div className="cc-footer">
        <span style={{ fontSize: 12, color: 'var(--muted)' }}>
          {c.profile.certifications.length > 0
            ? `${c.profile.certifications.length} certification${c.profile.certifications.length !== 1 ? 's' : ''}`
            : 'No certifications'}
        </span>
        <span className="cc-footer-link">View full report →</span>
      </div>
    </div>
  )
}

export default function ResultsPage() {
  const { run } = useApp()
  const [filter, setFilter] = useState('All')

  if (!run) return <><PageHead title="Candidate Results" /><NeedRun what="the results" /></>

  const counts: Record<string, number> = {
    All: run.candidates.length,
    Selected: run.summary.Selected,
    'Wait List': run.summary['Wait List'],
    Rejected: run.summary.Rejected,
  }

  const rows = [...run.candidates]
    .sort((a, b) => a.final.rank - b.final.rank)
    .filter(c => filter === 'All' || c.final.status === filter)

  return (
    <>
      <PageHead
        eyebrow="Step 4 of 4 · Shortlist"
        title="Candidate Results"
        desc={`Screening complete for "${run.job.title}". Click any card to see the full AI reasoning.`}
      />

      {/* Filter tabs with counts */}
      <div className="tabs">
        {(['All', 'Selected', 'Wait List', 'Rejected'] as const).map(f => (
          <button key={f} className={filter === f ? 'on' : ''} onClick={() => setFilter(f)}>
            {f} &nbsp;<span style={{ opacity: .7 }}>({counts[f]})</span>
          </button>
        ))}
      </div>

      {rows.length === 0 ? (
        <div className="card empty">
          <div className="big-ico"><span style={{ fontSize: 26 }}>🔍</span></div>
          <h3>No candidates in this category</h3>
          <p>Try a different filter above.</p>
        </div>
      ) : (
        <div className="cand-grid">
          {rows.map(c => <CandCard key={c.id} c={c} />)}
        </div>
      )}
    </>
  )
}
