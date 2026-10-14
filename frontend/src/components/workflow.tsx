import type { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useApp } from '../state'
import { Icon } from './icons'

/** The workflow starts with the resumes; the job requirements can be reviewed before (or after) starting. */
export const STEPS = [
  { no: 1, path: '/upload', title: 'Applications', sub: 'Upload resumes', nav: 'Applications' },
  { no: 2, path: '/job', title: 'Job Brief', sub: 'Role requirements', nav: 'Job Brief' },
  { no: 3, path: '/pipeline', title: 'AI Screening', sub: 'Run pipeline', nav: 'AI Screening' },
  { no: 4, path: '/results', title: 'Shortlist', sub: 'Review & decide', nav: 'Shortlist' },
] as const

export function stepOf(pathname: string): number {
  if (pathname.startsWith('/upload')) return 1
  if (pathname.startsWith('/job')) return 2
  if (pathname.startsWith('/pipeline')) return 3
  if (['/results', '/ranking', '/candidates', '/visualize', '/algorithms'].some(p => pathname.startsWith(p))) return 4
  return 0
}

/** Where the user is in the workflow, derived from real app state. */
export function useWorkflow() {
  const { candidates, run, stage } = useApp()
  const { pathname } = useLocation()
  const current = stepOf(pathname)
  const hasResumes = candidates.length > 0
  // Ticks show progress of THIS visit: nothing is ticked on arrival; steps tick as the workflow moves on.
  const done = { 1: stage !== 'idle', 2: stage !== 'idle', 3: stage === 'complete', 4: false } as Record<number, boolean>
  const locked = { 1: false, 2: false, 3: !hasResumes, 4: !run } as Record<number, boolean>
  return { current, done, locked, hasResumes, hasRun: !!run, candidates: candidates.length }
}

export function Stepper() {
  const { current, done, locked } = useWorkflow()
  return (
    <nav className="stepper" aria-label="Workflow">
      {STEPS.map((s, i) => {
        const cls = `st ${current === s.no ? 'current' : ''} ${done[s.no] && current !== s.no ? 'done' : ''} ${locked[s.no] ? 'locked' : ''}`
        const inner = (
          <>
            <span className="no">{done[s.no] && current !== s.no ? <Icon name="check" className="" /> : s.no}</span>
            <span><b>{s.title}</b><small>{s.sub}</small></span>
          </>
        )
        return (
          <span key={s.no} style={{ display: 'contents' }}>
            {locked[s.no] ? <span className={cls} title="Complete the previous step first">{inner}</span> : <Link className={cls} to={s.path}>{inner}</Link>}
            {i < STEPS.length - 1 && <span className={`bar-line ${done[s.no] ? 'done' : ''}`} />}
          </span>
        )
      })}
    </nav>
  )
}

/** Footer on each step: what to do next. */
export function PageFoot({ hint, children }: { hint: ReactNode; children: ReactNode }) {
  return <div className="page-foot"><div className="hint">{hint}</div><div className="row">{children}</div></div>
}
