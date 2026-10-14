import { useEffect, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api'
import { Icon } from '../components/icons'
import { PageHead } from '../components/ui'
import { PageFoot } from '../components/workflow'
import { useApp } from '../state'
import type { Job, JobOptions } from '../types'

/* ---------- small building blocks ---------- */
type Kind = 'must' | 'score' | 'rule'
const TAGS: Record<Kind, string> = { must: 'Must have', score: 'Adds to score', rule: 'Decision rule' }

function Field({ label, help, kind, children }: { label: string; help: ReactNode; kind?: Kind; children: ReactNode }) {
  return (
    <div className="jf">
      <div className="jf-top"><label>{label}</label>{kind && <span className={`tag ${kind}`}>{TAGS[kind]}</span>}</div>
      {children}
      <div className="jf-help">{help}</div>
    </div>
  )
}

function Section({ no, title, desc, children }: { no: string; title: string; desc: string; children: ReactNode }) {
  return (
    <div className="card section">
      <div className="sec-head"><span className="sec-no">{no}</span><div><h3>{title}</h3><div className="sub">{desc}</div></div></div>
      <div className="fields">{children}</div>
    </div>
  )
}

function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: [string, string][] }) {
  const opts = options.some(o => o[0] === value) ? options : [...options, [value, value] as [string, string]]
  return <select value={value} onChange={e => onChange(e.target.value)}>{opts.map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
}

/** Pick several values from a dropdown; picked values become removable chips. */
function MultiPick({ value, options, onChange, placeholder, custom }: {
  value: string[]; options: string[]; onChange: (v: string[]) => void; placeholder: string; custom?: string
}) {
  const [text, setText] = useState('')
  const add = (v: string) => { const t = v.trim(); if (t && !value.some(x => x.toLowerCase() === t.toLowerCase())) onChange([...value, t]) }
  return (
    <div>
      <div className="chips-box">
        {value.length === 0 && <span className="muted small">Nothing selected</span>}
        {value.map(v => <span key={v} className="chip-x">{v}<button type="button" aria-label={`Remove ${v}`} onClick={() => onChange(value.filter(x => x !== v))}>×</button></span>)}
      </div>
      <select value="" onChange={e => { if (e.target.value) add(e.target.value) }}>
        <option value="">{placeholder}</option>
        {options.filter(o => !value.some(x => x.toLowerCase() === o.toLowerCase())).map(o => <option key={o} value={o}>{o}</option>)}
      </select>
      {custom && (
        <div className="row" style={{ marginTop: 8, flexWrap: 'nowrap' }}>
          <input type="text" value={text} placeholder={custom} onChange={e => setText(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add(text); setText('') } }} />
          <button type="button" className="btn" onClick={() => { add(text); setText('') }}>Add</button>
        </div>
      )}
    </div>
  )
}

const range = (from: number, to: number, step: number) => Array.from({ length: Math.floor((to - from) / step) + 1 }, (_, i) => from + i * step)
const PRESETS = [
  { id: 'balanced', label: 'Balanced — skills 40 · experience 30 · projects 20 · certifications 10', w: { skills: .4, experience: .3, projects: .2, certifications: .1 } },
  { id: 'skills', label: 'Skills-first — skills 60 · experience 20 · projects 10 · certifications 10', w: { skills: .6, experience: .2, projects: .1, certifications: .1 } },
  { id: 'experience', label: 'Experience-first — skills 20 · experience 50 · projects 20 · certifications 10', w: { skills: .2, experience: .5, projects: .2, certifications: .1 } },
  { id: 'projects', label: 'Project-first — skills 20 · experience 20 · projects 50 · certifications 10', w: { skills: .2, experience: .2, projects: .5, certifications: .1 } },
]
const presetOf = (w: Job['weights']) => PRESETS.find(p => (['skills', 'experience', 'projects', 'certifications'] as const).every(k => Math.abs(p.w[k] - w[k]) < 0.001))?.id ?? 'custom'

/* ---------- page ---------- */
export default function JobPage() {
  const { job, setJob, candidates } = useApp()
  const nav = useNavigate()
  const [f, setF] = useState<Job | null>(null)
  const [opts, setOpts] = useState<JobOptions | null>(null)
  const [errors, setErrors] = useState<string[]>([])
  const [saved, setSaved] = useState(false)
  const [jd, setJd] = useState(''); const [jdMsg, setJdMsg] = useState<{ ok: boolean; text: string } | null>(null); const [jdBusy, setJdBusy] = useState(false)
  const [otherTitle, setOtherTitle] = useState(false); const [otherLoc, setOtherLoc] = useState(false); const [custom, setCustom] = useState(false)

  useEffect(() => { if (job) setF(job) }, [job])
  useEffect(() => { api.options().then(setOpts).catch(() => setOpts(null)) }, [])
  if (!f || !opts) return <p className="muted">Loading…</p>

  const set = <K extends keyof Job>(k: K, v: Job[K]) => { setF({ ...f, [k]: v }); setSaved(false) }
  const titleInList = opts.titles.includes(f.title)
  const locInList = !f.location || opts.locations.includes(f.location)
  const preset = custom ? 'custom' : presetOf(f.weights)

  async function autofill() {
    setJdBusy(true); setJdMsg(null)
    try {
      const r = await api.parseJd(jd)
      setF({ ...f!, ...r.suggestion } as Job); setSaved(false)
      setOtherTitle(false); setOtherLoc(false)
      setJdMsg({ ok: true, text: `Filled in: ${r.found.join(', ') || 'nothing'}.${r.not_found.length ? ` Not found in the text (set these yourself): ${r.not_found.join(', ')}.` : ''} Please review every dropdown below.` })
    } catch (e) { setJdMsg({ ok: false, text: e instanceof ApiError ? e.message : String(e) }) }
    finally { setJdBusy(false) }
  }

  async function save(): Promise<boolean> {
    setErrors([])
    try { const s = await api.saveJob(f!); setJob(s); setSaved(true); return true }
    catch (e) { setErrors(e instanceof ApiError ? e.details : [String(e)]); return false }
  }

  const mustList: string[] = []
  if (f.required_degrees.length) mustList.push(`Degree: ${f.required_degrees.join(' or ')}${f.degrees_equivalent && f.required_degrees.some(d => /^(B\.Tech|B\.E\.|M\.Tech|M\.E\.)$/.test(d)) ? ' (B.E. = B.Tech)' : ''}`)
  if (f.min_cgpa > 0) mustList.push(`CGPA of ${f.min_cgpa} or above`)
  mustList.push(f.min_experience > 0 ? `At least ${f.min_experience} year${f.min_experience === 1 ? '' : 's'} of experience` : 'Freshers are welcome (no experience needed)')
  if (f.skills_mandatory) mustList.push(`All of these skills: ${f.required_skills.join(', ') || '—'}`)
  if (f.location) mustList.push(`Based in ${f.location}`)
  if (f.certifications_mandatory && f.required_certifications.length) mustList.push(`Certification: ${f.required_certifications.join(', ')}`)
  const scoredList: string[] = []
  if (!f.skills_mandatory) scoredList.push(`Skills: ${f.required_skills.join(', ')}`)
  if (!f.certifications_mandatory && f.required_certifications.length) scoredList.push(`Certifications: ${f.required_certifications.join(', ')}`)
  scoredList.push('Experience, projects and skill match (see score weights)')

  return (
    <>
      <PageHead eyebrow="Step 2 of 4" title="Job requirements"
        desc="Describe who you are hiring by choosing from the dropdowns. Fields tagged “Must have” are pass/fail; the rest only change a candidate’s score."
        actions={<button className="btn" onClick={save}>Save</button>} />

      {errors.length > 0 && <div className="alert err"><div><b>Please fix:</b><ul>{errors.map((e, i) => <li key={i}>{e}</li>)}</ul></div></div>}
      {saved && <div className="alert ok">Saved. If you already ran the screening, run it again to apply the changes.</div>}

      <div className="job-layout">
        <div>
          <div className="card jd-box">
            <h3><span className="ico-chip"><Icon name="file" /></span>Have a job description already? <span className="muted small" style={{ fontWeight: 400 }}>(optional)</span></h3>
            <div className="sub">Paste it and the dropdowns below are filled in for you. This uses keyword matching only — no AI model — so always check the result.</div>
            <textarea rows={5} value={jd} onChange={e => setJd(e.target.value)}
              placeholder={'Example:\nBackend Developer\nB.E / B.Tech with 7.5 CGPA or above. 2 years of experience in Python, Java and SQL. AWS certification required. Location: Bengaluru. 3 openings.'} />
            <div className="row" style={{ marginTop: 10 }}>
              <button className="btn primary" disabled={jdBusy || jd.trim().length < 15} onClick={autofill}>{jdBusy ? 'Reading…' : 'Fill in the criteria from this description'}</button>
              {jdMsg && <span className={jdMsg.ok ? 'small' : 'small'} style={{ color: jdMsg.ok ? 'var(--pass)' : 'var(--fail)' }}>{jdMsg.text}</span>}
            </div>
          </div>

          <Section no="A" title="About the role" desc="What is the job and how many people do you need?">
            <Field label="Job title" help="Shown on the ranking and in reports.">
              <Select value={otherTitle || !titleInList ? '__other' : f.title} onChange={v => { if (v === '__other') { setOtherTitle(true) } else { setOtherTitle(false); set('title', v) } }}
                options={[...opts.titles.map(t => [t, t] as [string, string]), ['__other', 'Other (type it below)']]} />
              {(otherTitle || !titleInList) && <input type="text" style={{ marginTop: 8 }} value={f.title} placeholder="Type the job title" onChange={e => set('title', e.target.value)} />}
            </Field>
            <Field label="Number of openings" kind="rule" help="How many candidates can be marked “Selected”. Strong extras go to the Wait List.">
              <Select value={String(f.openings)} onChange={v => set('openings', Number(v))} options={range(1, 20, 1).map(n => [String(n), `${n} opening${n > 1 ? 's' : ''}`])} />
            </Field>
          </Section>

          <Section no="B" title="Education" desc="Which degree and academic score should candidates have?">
            <Field label="Accepted degrees" kind="must" help="A candidate needs ANY ONE of these. Pick several if they are equivalent (e.g. B.Tech and B.E.). Leave empty to accept any degree.">
              <MultiPick value={f.required_degrees} options={opts.degrees} onChange={v => set('required_degrees', v)} placeholder="+ Add a degree…" />
            </Field>
            <Field label="Are B.E. and B.Tech the same?" kind="must" help="Both are four-year engineering degrees. “Same” means a B.E. candidate passes a B.Tech job (and M.E. passes M.Tech) without you ticking both.">
              <Select value={f.degrees_equivalent ? 'yes' : 'no'} onChange={v => set('degrees_equivalent', v === 'yes')}
                options={[['yes', 'Yes — treat B.E. = B.Tech and M.E. = M.Tech (recommended)'], ['no', 'No — match the exact degree only']]} />
            </Field>
            <Field label="Minimum CGPA" kind="must" help="Out of 10. A candidate whose resume shows no CGPA fails this check.">
              <Select value={String(f.min_cgpa)} onChange={v => set('min_cgpa', Number(v))}
                options={[['0', 'No minimum'], ...range(6, 9, 0.5).map(n => [String(n), `${n.toFixed(1)} and above`] as [string, string])]} />
            </Field>
          </Section>

          <Section no="C" title="Experience" desc="How much work experience is needed?">
            <Field label="Minimum experience" kind="must" help="Counted from the dates or the “X years of experience” statement on the resume. More experience than this still earns full experience points.">
              <Select value={String(f.min_experience)} onChange={v => set('min_experience', Number(v))}
                options={[['0', 'Fresher — no experience needed'], ['0.5', '6 months'], ...[1, 2, 3, 4, 5, 7, 10].map(n => [String(n), `${n} year${n > 1 ? 's' : ''}`] as [string, string])]} />
            </Field>
          </Section>

          <Section no="D" title="Skills and certifications" desc="What must the candidate know?">
            <Field label="Required skills" kind={f.skills_mandatory ? 'must' : 'score'} help="Pick from the list or type your own. Python and python are treated as the same skill.">
              <MultiPick value={f.required_skills} options={opts.skills} onChange={v => set('required_skills', v)} placeholder="+ Add a skill…" custom="Not in the list? Type a skill" />
            </Field>
            <Field label="How strict are skills?" kind="rule" help="“All required” rejects anyone who misses even one skill. “Score only” just gives fewer points.">
              <Select value={f.skills_mandatory ? 'all' : 'score'} onChange={v => set('skills_mandatory', v === 'all')}
                options={[['all', 'All required skills must be present'], ['score', 'Skills only add to the score']]} />
            </Field>
            <Field label="Certifications" kind={f.certifications_mandatory ? 'must' : 'score'} help="Optional. E.g. an AWS certificate on the resume.">
              <MultiPick value={f.required_certifications} options={opts.certifications} onChange={v => set('required_certifications', v)} placeholder="+ Add a certification…" custom="Not in the list? Type a certification" />
            </Field>
            <Field label="How strict are certifications?" kind="rule" help="“Required” rejects candidates without them; “Preferred” only adds score.">
              <Select value={f.certifications_mandatory ? 'req' : 'pref'} onChange={v => set('certifications_mandatory', v === 'req')}
                options={[['pref', 'Preferred — adds to the score'], ['req', 'Required — candidates without it are rejected']]} />
            </Field>
          </Section>

          <Section no="E" title="Location" desc="Where will the person work?">
            <Field label="Work location" kind={f.location ? 'must' : undefined} help="If you pick a city, candidates whose resume shows a different (or no) location are rejected by the constraint check.">
              <Select value={otherLoc || !locInList ? '__other' : f.location ?? ''} onChange={v => { if (v === '__other') setOtherLoc(true); else { setOtherLoc(false); set('location', v || null) } }}
                options={[['', 'Anywhere — no location rule'], ...opts.locations.map(l => [l, l] as [string, string]), ['__other', 'Other (type it below)']]} />
              {(otherLoc || !locInList) && <input type="text" style={{ marginTop: 8 }} value={f.location ?? ''} placeholder="Type the city" onChange={e => set('location', e.target.value || null)} />}
            </Field>
          </Section>

          <Section no="F" title="How decisions are made" desc="What counts most, and what score earns which result?">
            <Field label="What matters most?" kind="score" help="Sets how much skills, experience, projects and certifications count in the 0–100 score.">
              <Select value={preset} onChange={v => { if (v === 'custom') setCustom(true); else { setCustom(false); set('weights', PRESETS.find(p => p.id === v)!.w) } }}
                options={[...PRESETS.map(p => [p.id, p.label] as [string, string]), ['custom', 'Custom…']]} />
              {preset === 'custom' && (
                <div className="grid g4" style={{ gap: 8, marginTop: 8 }}>
                  {(['skills', 'experience', 'projects', 'certifications'] as const).map(k => (
                    <label key={k} className="small muted" style={{ textTransform: 'capitalize' }}>{k} %
                      <input type="number" min={0} max={100} value={Math.round(f.weights[k] * 100)} onChange={e => set('weights', { ...f.weights, [k]: Number(e.target.value) / 100 })} /></label>))}
                </div>)}
            </Field>
            <div />
            <Field label="“Selected” if the score is at least" kind="rule" help="A candidate must reach this AND be chosen by the search for an opening.">
              <Select value={String(f.thresholds.selected)} onChange={v => set('thresholds', { ...f.thresholds, selected: Number(v) })} options={range(50, 100, 5).reverse().map(n => [String(n), `${n} / 100`])} />
            </Field>
            <Field label="“Wait List” if the score is at least" kind="rule" help="Below this score the candidate is rejected.">
              <Select value={String(f.thresholds.waitlist)} onChange={v => set('thresholds', { ...f.thresholds, waitlist: Number(v) })} options={range(30, 95, 5).reverse().map(n => [String(n), `${n} / 100`])} />
            </Field>
          </Section>
        </div>

        <aside className="sticky">
          <div className="card summary">
            <h3><span className="ico-chip"><Icon name="target" /></span>Your job in one glance</h3>
            <p className="lead">
              Hiring <b>{f.openings}</b> <b>{f.title}</b>{f.openings > 1 ? 's' : ''}{f.location ? <> in <b>{f.location}</b></> : ' (any location)'}.
            </p>
            <div className="sum-title must">Candidates must have</div>
            <ul className="sum-list">{mustList.map(m => <li key={m}>{m}</li>)}</ul>
            <div className="sum-title score">Only adds to their score</div>
            <ul className="sum-list">{scoredList.map(m => <li key={m}>{m}</li>)}</ul>
            <div className="sum-title rule">Result for each candidate</div>
            <ul className="sum-list">
              <li><b>Selected</b> — score ≥ {f.thresholds.selected} and chosen for an opening</li>
              <li><b>Wait List</b> — score {f.thresholds.waitlist}–{f.thresholds.selected} (or openings are full)</li>
              <li><b>Rejected</b> — fails a “must have”, or score below {f.thresholds.waitlist}</li>
            </ul>
          </div>
        </aside>
      </div>

      <PageFoot hint={candidates.length ? `${candidates.length} resume(s) are waiting. Save your changes and start the workflow.` : 'Next: add the resumes you want to screen.'}>
        {candidates.length > 0
          ? <button className="btn primary lg" onClick={async () => { if (await save()) nav('/pipeline', { state: { autorun: true } }) }}>Save &amp; start workflow →</button>
          : <button className="btn primary lg" onClick={async () => { if (await save()) nav('/upload') }}>Save &amp; add resumes →</button>}
      </PageFoot>
    </>
  )
}
