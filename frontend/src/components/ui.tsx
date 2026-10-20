import { useEffect, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useApp } from '../state'
import type { Stage } from '../types'
import { Icon } from './icons'

export function Badge({ status }: { status: string }) {
  const s = status.toLowerCase()
  const cls = s === 'pass' || s === 'selected' || s === 'proven' || s === 'valid' || s === 'eligible' ? 'b-pass'
    : s === 'fail' || s === 'rejected' || s === 'failed' ? 'b-fail'
    : s.startsWith('wait') ? 'b-wait' : s === 'skipped' ? 'b-skipped' : 'b-neutral'
  return <span className={`badge ${cls}`}>{status.toUpperCase()}</span>
}

export function PageHead({ title, desc, actions, eyebrow }: { title: string; desc?: ReactNode; actions?: ReactNode; eyebrow?: string }) {
  return (
    <div className="page-head">
      <div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1>{desc && <p>{desc}</p>}</div>
      {actions && <div className="row">{actions}</div>}
    </div>
  )
}

export function Card({ title, sub, children, right, icon }: { title?: ReactNode; sub?: ReactNode; children: ReactNode; right?: ReactNode; icon?: string; lift?: boolean }) {
  return (
    <div className="card">
      {(title || right) && <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'nowrap' }}>
        <div>{title && <h3>{icon && <span className="ico-chip"><Icon name={icon} /></span>}{title}</h3>}{sub && <div className="sub" style={{ marginTop: 4 }}>{sub}</div>}</div>{right}
      </div>}
      {children}
    </div>
  )
}

/** Animated number that counts up when it changes. */
export function CountUp({ value }: { value: number }) {
  const [n, setN] = useState(0)
  useEffect(() => {
    const start = performance.now(); const from = 0
    let raf = 0
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / 700)
      setN(Math.round(from + (value - from) * (1 - Math.pow(1 - p, 3))))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value])
  return <>{n}</>
}

export function Kpi({ label, value, hint, tone, icon }: { label: string; value: ReactNode; hint?: string; tone?: string; icon?: string }) {
  return (
    <div className="card kpi">
      <div className="top"><div className="label">{label}</div>{icon && <div className="ic" style={tone ? { color: tone, background: 'var(--skip-bg)' } : undefined}><Icon name={icon} /></div>}</div>
      <div className="value" style={tone ? { color: tone } : undefined}>{value}</div>
      {hint && <div className="hint">{hint}</div>}
    </div>
  )
}

export function ErrorBanner() {
  const { error, setError } = useApp()
  if (!error) return null
  return (
    <div className="alert err" role="alert">
      <div><b>Something went wrong.</b> {error}</div>
      <button className="btn sm" onClick={() => setError(null)}>Dismiss</button>
    </div>
  )
}

export function Empty({ title, children, icon = 'file' }: { title: string; children?: ReactNode; icon?: string }) {
  return <div className="card empty"><div className="big-ico"><Icon name={icon} /></div><h3>{title}</h3><div>{children}</div></div>
}

export function NeedRun({ what = 'this page' }: { what?: string }) {
  const { candidates, run, running, runPipeline, loadSamples } = useApp()
  if (run) return null
  return (
    <Empty title="Nothing to show yet" icon="pipeline">
      <p>{candidates.length === 0 ? `Upload resumes (or load the sample data) and run the pipeline to populate ${what}.`
        : `You have ${candidates.length} resume(s). Run the pipeline to populate ${what}.`}</p>
      <div className="row" style={{ justifyContent: 'center' }}>
        {candidates.length === 0 && <button className="btn" onClick={loadSamples}>Load sample data</button>}
        {candidates.length > 0 && <button className="btn primary" disabled={running} onClick={runPipeline}>{running ? 'Running…' : 'Run pipeline'}</button>}
        <Link className="btn" to="/upload">Go to upload</Link>
      </div>
    </Empty>
  )
}

export const PIPELINE_FLOW = [
  ['parsing', 'Parsing'], ['bfs_dfs', 'BFS / DFS'], ['heuristic', 'Heuristic'], ['local_search', 'Local Search'],
  ['csp', 'CSP'], ['forward_chaining', 'Forward Chaining'], ['backward_chaining', 'Backward Chaining'],
  ['alpha_beta', 'Alpha-Beta'], ['game_tree', 'Game Tree'], ['ranking', 'Final Ranking'],
] as const

export function PipelineFlow({ stages, activeIndex }: { stages?: Stage[]; activeIndex?: number }) {
  const done = new Set((stages ?? []).map(s => s.id))
  return (
    <div className="flow">
      <span className="node plain">Job + Resumes</span><span className="arrow" />
      {PIPELINE_FLOW.map(([id, label], i) => (
        <span key={id} style={{ display: 'contents' }}>
          <span className={`node ${activeIndex !== undefined ? (i < activeIndex ? 'done' : i === activeIndex ? 'active' : '') : done.has(id) ? 'done' : ''}`}>
            <i>{done.has(id) ? '✓' : i + 1}</i>{label}
          </span>
          <span className="arrow" />
        </span>
      ))}
      <span className="node plain">HR Review</span>
    </div>
  )
}

export function Avatar({ name, large }: { name: string; large?: boolean }) {
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase()
  return <div className={`avatar ${large ? 'lg' : ''}`}>{initials}</div>
}

export function statusColor(status: string) {
  return status === 'Selected' ? '#16a34a' : status === 'Wait List' ? '#f5a623' : '#dc2626'
}

export function ScoreRing({ value, size = 120, color = '#6366f1', label = 'score' }: { value: number | null; size?: number; color?: string; label?: string }) {
  const [v, setV] = useState(0)
  useEffect(() => { const t = setTimeout(() => setV(value ?? 0), 80); return () => clearTimeout(t) }, [value])
  const r = (size - 14) / 2; const c = 2 * Math.PI * r
  return (
    <div className="ring" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle className="track" cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth="10" />
        <circle className="val" cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth="10" strokeLinecap="round" stroke={color}
          strokeDasharray={c} strokeDashoffset={c * (1 - Math.min(v, 100) / 100)} />
      </svg>
      <div className="txt"><b style={size < 80 ? { fontSize: Math.round(size * 0.34) } : undefined}>{value === null ? '—' : Number(value.toFixed(1))}</b>{label && <small>{label}</small>}</div>
    </div>
  )
}

export function ScoreBar({ value, color }: { value: number | null; color?: string }) {
  if (value === null) return <span className="muted">—</span>
  return (
    <div className="scorebar"><b>{Number(value.toFixed(1))}</b>
      <div className="bar"><i style={{ width: `${Math.min(value, 100)}%`, background: color ?? undefined }} /></div></div>
  )
}

export const fmt = (n: number | null | undefined, d = 1) => (n === null || n === undefined ? '—' : Number(n.toFixed(d)).toString())
