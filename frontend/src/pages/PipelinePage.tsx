import { useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Icon } from '../components/icons'
import { Card, NeedRun, PageHead } from '../components/ui'
import { PageFoot } from '../components/workflow'
import { useApp } from '../state'

const STEP_MS = 900  // how long each finished step stays on screen before the next one starts

const WHY: Record<string, string> = {
  parsing: 'Turns PDF/DOCX text into structured data with regex + dictionaries.',
  bfs_dfs: 'Checks the mandatory criteria tree. Ineligible candidates stop here — they never reach the expensive stages.',
  heuristic: 'Scores each eligible candidate with the weighted heuristic and orders them with a priority queue.',
  local_search: 'Hill-climbs the ordering by swapping adjacent candidates while the objective improves.',
  csp: 'Validates every hard constraint (including location & mandatory certifications).',
  forward_chaining: 'Derives “eligible” from the candidate’s facts by firing IF-THEN rules.',
  backward_chaining: 'Starts at the goal “eligible?” and verifies each prerequisite, naming any that fail.',
  alpha_beta: 'Searches the candidate game tree and prunes branches that cannot beat the current best.',
  game_tree: 'MAX = HR picks a candidate; MIN = a panel judges its worst-case viewpoint.',
  ranking: 'Applies the configurable thresholds and produces the ranked list.',
}

export default function PipelinePage() {
  const { run, running, candidates, runPipeline, setStage } = useApp()
  const location = useLocation()
  const nav = useNavigate()
  const [playing, setPlaying] = useState(false)   // true while the steps are being revealed one by one
  const [shown, setShown] = useState(0)           // how many steps have finished so far
  const timer = useRef<number | undefined>(undefined)
  const autoStarted = useRef(false)
  const playingRef = useRef(false)
  useEffect(() => { playingRef.current = playing }, [playing])

  const total = run?.stages.length ?? 10
  const finished = playing ? shown : total        // not playing = show the completed workflow as it is
  const pct = Math.round((finished / total) * 100)

  const reveal = (n: number) => {
    window.clearInterval(timer.current)
    let i = 0
    setShown(0); setPlaying(true)
    timer.current = window.setInterval(() => {
      i += 1; setShown(i)
      if (i >= n) {
        window.clearInterval(timer.current)
        setPlaying(false)
        setStage('complete')
        setTimeout(() => nav('/live-review'), 800)
      }
    }, STEP_MS)
  }

  async function start() {
    window.clearInterval(timer.current)
    setShown(0); setPlaying(true); setStage('running')   // steps show as waiting while the server does the work
    const r = await runPipeline()
    if (r) reveal(r.stages.length); else { setPlaying(false); setStage('idle') }
  }

  const skip = () => { window.clearInterval(timer.current); setPlaying(false); setStage('complete') }

  // Arriving from a "Start workflow" button: run immediately (only once, even in React strict mode).
  useEffect(() => {
    const wanted = (location.state as { autorun?: boolean } | null)?.autorun || new URLSearchParams(location.search).get('autorun') === '1'
    if (wanted && candidates.length && !autoStarted.current) {
      autoStarted.current = true
      window.history.replaceState({}, '', location.pathname)   // a page refresh must not start another run
      void start()
    }
    // Leaving mid-animation: the server already has the full result, so the workflow counts as complete.
    return () => { window.clearInterval(timer.current); if (playingRef.current) setStage('complete') }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const complete = !!run && !playing
  const current = run?.stages[Math.min(shown, total - 1)]

  return (
    <>
      <PageHead eyebrow="Step 3 of 4" title="Run workflow"
        desc="Watch every stage run in order. Each one turns green when it is finished, showing how many candidates went in and came out."
        actions={complete || !run
          ? <button className="btn primary" disabled={running || candidates.length === 0} onClick={start}><Icon name="play" />{run ? 'Run again' : 'Start workflow'}</button>
          : <button className="btn" onClick={skip}>Skip animation</button>} />

      {candidates.length === 0 && <div className="alert info">No resumes yet. <Link to="/upload">Upload resumes</Link> first, then start the workflow.</div>}

      {!run && !playing ? <NeedRun what="the workflow" /> : (
        <>
          <div className="card progress-card">
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <div>
                <b>{playing ? (running ? 'Reading the resumes…' : `Running step ${Math.min(shown + 1, total)} of ${total}: ${current?.label ?? ''}`) : 'Workflow complete'}</b>
                <div className="small muted">{playing ? current?.algorithm : `${run?.summary.total} candidates screened for “${run?.job.title}”`}</div>
              </div>
              <div className="progress-pct">{playing ? pct : 100}%</div>
            </div>
            <div className="bar lg"><i style={{ width: `${playing ? pct : 100}%` }} /></div>
          </div>

          <div style={{ height: 16 }} />
          <Card title="Stage by stage" icon="list" sub={run ? `${run.summary.total} candidates in → ${run.summary.Selected} selected` : undefined}>
            <div className="timeline">
              {(run?.stages ?? []).map((s, i) => {
                const state = i < finished ? 'done' : (playing && !running && i === finished) ? 'active' : 'wait'
                return (
                  <div key={s.id} className={`stage ${state === 'wait' ? '' : state}`}>
                    <div className="dot">{state === 'done' ? '✓' : state === 'active' ? <span className="spinner" /> : i + 1}</div>
                    <div>
                      <h4>{s.label} <span className="muted small" style={{ fontWeight: 500 }}>· {s.algorithm}</span></h4>
                      <div className="out">{state === 'done' ? s.summary : state === 'active' ? <span className="running">Running…</span> : <span className="muted">Waiting</span>}</div>
                      <div className="meta">{WHY[s.id]}</div>
                    </div>
                    <div className="counts">
                      {state === 'done' && <><span className="pair">{s.input}<span>→</span>{s.output}</span>
                        <div className="small muted" style={{ marginTop: 4 }}>{s.ms ? `${s.ms} ms` : ''}</div></>}
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>
        </>
      )}

      {complete && (
        <PageFoot hint={<><b>Workflow complete.</b> {run!.summary.Selected} selected, {run!.summary['Wait List']} wait-listed, {run!.summary.Rejected} rejected.</>}>
          <Link className="btn" to="/visualize">See how it decided</Link>
          <Link className="btn primary" to="/live-review"><Icon name="play" /> Watch Live Review</Link>
          <Link className="btn primary lg" to="/ranking">Review the ranking →</Link>
        </PageFoot>
      )}
    </>
  )
}
