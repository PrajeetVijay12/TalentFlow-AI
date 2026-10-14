import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Icon } from '../components/icons'
import { Avatar, Badge, ScoreRing, statusColor } from '../components/ui'
import { useApp } from '../state'
import type { CandidateResult } from '../types'

const SCAN_MS = 1200
const FIELD_DELAY = 350
const PER_FIELD_MS = 170
const HOLD_MS = 700

function candidateTotalMs(fieldCount: number) {
  return SCAN_MS + FIELD_DELAY + fieldCount * PER_FIELD_MS + HOLD_MS
}

function ReviewCard({ c, isActive }: { c: CandidateResult; isActive: boolean }) {
  const [scanDone, setScanDone] = useState(false)
  const [fieldCount, setFieldCount] = useState(0)
  const status = c.final.status
  const ccCls = status === 'Selected' ? 'cc-selected' : status === 'Wait List' ? 'cc-wait' : 'cc-rejected'
  const icon = status === 'Selected' ? '✅' : status === 'Wait List' ? '⏳' : '❌'
  const fields = [
    { label: 'Degree', value: c.profile.degree ?? null },
    { label: 'CGPA', value: c.profile.cgpa?.toString() ?? null },
    { label: 'Experience', value: `${c.profile.experience} yr` },
    { label: 'Location', value: c.profile.location ?? 'Any' },
  ].filter(f => f.value !== null) as { label: string; value: string }[]

  useEffect(() => {
    if (!isActive) return
    const t1 = setTimeout(() => setScanDone(true), SCAN_MS)
    let i = 0
    const revealNext = () => {
      if (i < fields.length) {
        i++; setFieldCount(i)
        setTimeout(revealNext, PER_FIELD_MS)
      }
    }
    const t2 = setTimeout(revealNext, SCAN_MS + FIELD_DELAY)
    return () => { clearTimeout(t1); clearTimeout(t2) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive])

  const showVerdict = fieldCount >= fields.length && scanDone

  return (
    <div className={`lr-card ${ccCls}`}>
      {/* Scanning beam */}
      {isActive && !scanDone && <div className="scan-line" />}

      {/* Header */}
      <div className="lr-card-header">
        <Avatar name={c.name} large />
        <div style={{ flex: 1, minWidth: 0 }}>
          <h2 className="lr-name">{c.name}</h2>
          <div className="lr-sub">{c.profile.degree ?? 'Unknown degree'} · {c.profile.location ?? 'Unknown location'}</div>
          <div className="lr-sub" style={{ marginTop: 4 }}>
            {isActive && !scanDone && <span className="lr-scanning">🔍 Scanning resume…</span>}
            {scanDone && fieldCount < fields.length && <span style={{ color: 'var(--accent)', fontWeight: 600 }}>Extracting profile data…</span>}
            {showVerdict && <span style={{ color: 'var(--muted)' }}>Analysis complete</span>}
          </div>
        </div>
        <AnimatePresence>
          {showVerdict && (
            <motion.div
              initial={{ scale: 0, rotate: -20 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 450, damping: 18 }}>
              <Badge status={status} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Extracted fields */}
      <div className="lr-fields">
        {fields.slice(0, fieldCount).map(f => (
          <motion.div key={f.label}
            initial={{ opacity: 0, x: -18 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.28 }}
            className="lr-field-row">
            <span className="lr-check">✓</span>
            <span className="lr-field-label">{f.label}</span>
            <span className="lr-field-val">{f.value}</span>
          </motion.div>
        ))}
        {/* Placeholder rows */}
        {fields.slice(fieldCount).map(f => (
          <div key={f.label} className="lr-field-row lr-field-pending">
            <span className="lr-check-pending">○</span>
            <span className="lr-field-label">{f.label}</span>
            <span style={{ color: 'var(--line)', fontStyle: 'italic', fontSize: 12 }}>—</span>
          </div>
        ))}
      </div>

      {/* Score + verdict */}
      <AnimatePresence>
        {showVerdict && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="lr-verdict-row">
            <ScoreRing value={c.final.score} size={72} color={statusColor(status)} label="score" />
            <div style={{ flex: 1 }}>
              <div className={`cc-decision ${ccCls}`}>
                <span className="cd-icon">{icon}</span>
                <span>{c.final.reasons[0] ?? '—'}</span>
              </div>
              {c.profile.skills.length > 0 && (
                <div className="cc-skills" style={{ marginTop: 10 }}>
                  {c.profile.skills.slice(0, 4).map(s => <span key={s} className="chip">{s}</span>)}
                  {c.profile.skills.length > 4 && <span className="chip">+{c.profile.skills.length - 4}</span>}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default function LiveReviewPage() {
  const { run } = useApp()
  const nav = useNavigate()
  const [current, setCurrent] = useState(0)
  const [done, setDone] = useState(false)
  const [reviewed, setReviewed] = useState<CandidateResult[]>([])
  const timerRef = useRef<number | undefined>(undefined)

  // Sort by rank so HR sees best candidates first revealed
  const candidates = [...(run?.candidates ?? [])].sort((a, b) => a.final.rank - b.final.rank)

  useEffect(() => {
    if (!run || candidates.length === 0) { nav('/pipeline'); return }

    function reviewNext(idx: number) {
      if (idx >= candidates.length) { setDone(true); return }
      setCurrent(idx)
      const c = candidates[idx]
      const fieldCount = [c.profile.degree, c.profile.cgpa, c.profile.experience, c.profile.location].filter(Boolean).length
      const wait = candidateTotalMs(Math.min(fieldCount, 4))
      timerRef.current = window.setTimeout(() => {
        setReviewed(prev => [...prev, candidates[idx]])
        reviewNext(idx + 1)
      }, wait)
    }

    reviewNext(0)
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (!run) return null

  const total = candidates.length
  const pct = done ? 100 : Math.round((current / total) * 100)

  return (
    <>
      {/* Header */}
      <div className="page-head">
        <div>
          <div className="eyebrow">Live Review</div>
          <h1>AI Resume Screening</h1>
          <p style={{ marginTop: 4 }}>
            {done
              ? `All ${total} candidates reviewed — ${run.summary.Selected} shortlisted, ${run.summary['Wait List']} wait-listed, ${run.summary.Rejected} rejected.`
              : `Reviewing candidate ${current + 1} of ${total} for "${run.job.title}"…`}
          </p>
        </div>
        {done && (
          <div className="row">
            <Link className="btn" to="/results"><Icon name="users" /> All Candidates</Link>
            <Link className="btn primary lg" to="/ranking"><Icon name="trophy" /> View Shortlist →</Link>
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div className="lr-progress-bar">
        <div className="lr-prog-fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="lr-prog-labels">
        <span>{done ? 'Screening complete' : `Processing ${current + 1} / ${total}`}</span>
        <span style={{ fontWeight: 700 }}>{pct}%</span>
      </div>

      {/* Main layout */}
      <div className="lr-layout">

        {/* Active card */}
        <div className="lr-active-panel">
          <div className="lr-panel-label">
            {done ? '🎯 Screening Complete' : '🔬 Now Reviewing'}
          </div>
          <AnimatePresence mode="wait">
            {!done ? (
              <motion.div key={current}
                initial={{ opacity: 0, x: 60, scale: 0.96 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: -60, scale: 0.96 }}
                transition={{ duration: 0.38, ease: 'easeOut' }}>
                <ReviewCard c={candidates[current]} isActive={true} />
              </motion.div>
            ) : (
              <motion.div key="done"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.45 }}
                className="card lr-done-card">
                <div className="lr-done-emoji">🎯</div>
                <h2>Screening Complete!</h2>
                <p style={{ color: 'var(--muted)', marginTop: 8, marginBottom: 20 }}>
                  All {total} candidates processed for "{run.job.title}"
                </p>
                <div className="hire-funnel" style={{ margin: 0 }}>
                  <div className="hf-stage hf-total">
                    <div className="hf-label">Total</div>
                    <div className="hf-val">{run.summary.total}</div>
                  </div>
                  <div className="hf-stage hf-eligible">
                    <div className="hf-label">Eligible</div>
                    <div className="hf-val">{run.summary.eligible}</div>
                  </div>
                  <div className="hf-stage hf-selected">
                    <div className="hf-label">Shortlisted</div>
                    <div className="hf-val">{run.summary.Selected}</div>
                  </div>
                  <div className="hf-stage hf-rejected">
                    <div className="hf-label">Rejected</div>
                    <div className="hf-val">{run.summary.Rejected}</div>
                  </div>
                </div>
                <div className="row" style={{ justifyContent: 'center', marginTop: 20 }}>
                  <Link className="btn" to="/results"><Icon name="users" /> All Candidates</Link>
                  <Link className="btn primary lg" to="/ranking"><Icon name="trophy" /> View Shortlist →</Link>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Reviewed queue */}
        <div className="lr-queue-panel">
          <div className="lr-panel-label">Reviewed ({reviewed.length}/{total})</div>
          <div className="lr-queue-list">
            <AnimatePresence initial={false}>
              {[...reviewed].reverse().map(c => {
                const status = c.final.status
                const qIcon = status === 'Selected' ? '✅' : status === 'Wait List' ? '⏳' : '❌'
                const ccCls = status === 'Selected' ? 'cc-selected' : status === 'Wait List' ? 'cc-wait' : 'cc-rejected'
                return (
                  <motion.div key={c.id}
                    initial={{ opacity: 0, y: -24 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.32 }}
                    className={`lr-mini-card ${ccCls}`}>
                    <Avatar name={c.name} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div className="lr-mini-name">{c.name}</div>
                      <div className="lr-mini-sub">
                        Score: <strong style={{ color: statusColor(status) }}>{c.final.score?.toFixed(1) ?? '—'}</strong>
                        {' · '}Rank #{c.final.rank}
                      </div>
                    </div>
                    <span className="lr-mini-icon">{qIcon}</span>
                  </motion.div>
                )
              })}
            </AnimatePresence>
            {reviewed.length === 0 && (
              <div style={{ textAlign: 'center', padding: '28px 16px', color: 'var(--muted)', fontSize: 13 }}>
                <div style={{ fontSize: 28, marginBottom: 8 }}>⏳</div>
                Candidates will appear here as they're reviewed…
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
