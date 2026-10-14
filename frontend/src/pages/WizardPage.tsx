import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api'
import { Icon } from '../components/icons'
import { useApp } from '../state'
import type { Job, JobOptions } from '../types'

const DEGREES = ['B.Tech', 'B.E.', 'BCA', 'B.Sc', 'MCA', 'M.Tech', 'MBA']
const COMMON_TITLES = ['Software Engineer', 'Backend Developer', 'Full Stack Developer', 'Frontend Developer', 'Data Analyst', 'DevOps Engineer', 'QA Engineer', 'Mobile Developer']

type Draft = {
  title: string
  required_degrees: string[]
  degrees_equivalent: boolean
  min_cgpa: number
  min_experience: number
  required_skills: string[]
  required_certifications: string[]
  certifications_mandatory: boolean
  skills_mandatory: boolean
  location: string | null
  openings: number
  thresholds: { selected: number; waitlist: number }
}

const INITIAL: Draft = {
  title: '', required_degrees: ['B.Tech'], degrees_equivalent: true,
  min_cgpa: 7.5, min_experience: 1, required_skills: [], required_certifications: [],
  certifications_mandatory: false, skills_mandatory: true,
  location: null, openings: 2, thresholds: { selected: 85, waitlist: 70 },
}

const STEPS = [
  { id: 'title', label: 'Role', icon: '💼' },
  { id: 'degree', label: 'Degree', icon: '🎓' },
  { id: 'cgpa', label: 'CGPA', icon: '📊' },
  { id: 'experience', label: 'Experience', icon: '⏳' },
  { id: 'skills', label: 'Skills', icon: '🛠️' },
  { id: 'certifications', label: 'Certs', icon: '🏅' },
  { id: 'location', label: 'Location', icon: '📍' },
  { id: 'openings', label: 'Openings', icon: '🎯' },
]

export default function WizardPage() {
  const [step, setStep] = useState(0)
  const [draft, setDraft] = useState<Draft>(INITIAL)
  const [options, setOptions] = useState<JobOptions | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [skillInput, setSkillInput] = useState('')
  const [certInput, setCertInput] = useState('')
  const [anyLocation, setAnyLocation] = useState(true)
  const { candidates, refresh, resetProgress, setError: appError } = useApp()
  const nav = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.options().then(setOptions).catch(() => {})
    setTimeout(() => inputRef.current?.focus(), 100)
  }, [step])

  const set = (patch: Partial<Draft>) => setDraft(d => ({ ...d, ...patch }))

  function addSkill(s: string) {
    const trimmed = s.trim()
    if (!trimmed) return
    if (draft.required_skills.map(x => x.toLowerCase()).includes(trimmed.toLowerCase())) return
    set({ required_skills: [...draft.required_skills, trimmed] })
    setSkillInput('')
  }

  function addCert(s: string) {
    const trimmed = s.trim()
    if (!trimmed) return
    if (draft.required_certifications.map(x => x.toLowerCase()).includes(trimmed.toLowerCase())) return
    set({ required_certifications: [...draft.required_certifications, trimmed] })
    setCertInput('')
  }

  function canNext() {
    if (step === 0) return draft.title.trim().length > 0
    if (step === 4) return draft.required_skills.length > 0
    return true
  }

  async function finish() {
    setSaving(true); setError(null)
    try {
      const jobPayload: Partial<Job> = {
        title: draft.title, required_degrees: draft.required_degrees,
        degrees_equivalent: draft.degrees_equivalent,
        min_cgpa: draft.min_cgpa, min_experience: draft.min_experience,
        required_skills: draft.required_skills,
        required_certifications: draft.required_certifications,
        certifications_mandatory: draft.certifications_mandatory,
        skills_mandatory: draft.skills_mandatory,
        location: anyLocation ? null : (draft.location || null),
        openings: draft.openings,
        thresholds: draft.thresholds,
      } as Job
      await api.saveJob(jobPayload as Job)
      if (candidates.length > 0) {
        await api.clearCandidates()
        resetProgress()
        await refresh()
      }
      nav('/upload')
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  const suggestedSkills = (options?.skills ?? []).filter(s =>
    !draft.required_skills.map(x => x.toLowerCase()).includes(s.toLowerCase()) &&
    (!skillInput || s.toLowerCase().includes(skillInput.toLowerCase()))
  ).slice(0, 8)

  const suggestedCerts = (options?.certifications ?? []).filter(c =>
    !draft.required_certifications.map(x => x.toLowerCase()).includes(c.toLowerCase()) &&
    (!certInput || c.toLowerCase().includes(certInput.toLowerCase()))
  ).slice(0, 6)

  return (
    <div className="wiz-wrap">
      {/* Progress bar */}
      <div className="wiz-progress">
        {STEPS.map((s, i) => (
          <div key={s.id} className={`wiz-step ${i < step ? 'done' : i === step ? 'active' : 'todo'}`}>
            <div className="wiz-dot">
              {i < step ? '✓' : <span>{s.icon}</span>}
            </div>
            <div className="wiz-step-label">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Card */}
      <div className="wiz-card">
        {error && <div className="alert err" style={{ marginBottom: 16 }}>{error}</div>}

        {/* Step 0 — Job Title */}
        {step === 0 && (
          <div className="wiz-step-body">
            <div className="wiz-question">What role are you hiring for?</div>
            <div className="wiz-hint">Give this recruitment a title — it will appear in the shortlist and history.</div>
            <input ref={inputRef} type="text" className="wiz-big-input" value={draft.title}
              onChange={e => set({ title: e.target.value })}
              onKeyDown={e => e.key === 'Enter' && canNext() && setStep(1)}
              placeholder="e.g. Junior Software Developer" />
            <div className="wiz-chips-row">
              {COMMON_TITLES.map(t => (
                <button key={t} className={`wiz-suggest ${draft.title === t ? 'active' : ''}`}
                  onClick={() => set({ title: t })}>{t}</button>
              ))}
            </div>
          </div>
        )}

        {/* Step 1 — Degree */}
        {step === 1 && (
          <div className="wiz-step-body">
            <div className="wiz-question">What degree is required?</div>
            <div className="wiz-hint">Select all accepted degrees. Candidates without these are rejected.</div>
            <div className="wiz-checkbox-grid">
              {DEGREES.map(d => (
                <label key={d} className={`wiz-check-card ${draft.required_degrees.includes(d) ? 'active' : ''}`}>
                  <input type="checkbox" checked={draft.required_degrees.includes(d)}
                    onChange={e => set({ required_degrees: e.target.checked ? [...draft.required_degrees, d] : draft.required_degrees.filter(x => x !== d) })} />
                  {d}
                </label>
              ))}
            </div>
            <label className="wiz-toggle-row">
              <input type="checkbox" checked={draft.degrees_equivalent}
                onChange={e => set({ degrees_equivalent: e.target.checked })} />
              <span>Accept equivalent degrees (B.E. = B.Tech, M.E. = M.Tech)</span>
            </label>
          </div>
        )}

        {/* Step 2 — CGPA */}
        {step === 2 && (
          <div className="wiz-step-body">
            <div className="wiz-question">Minimum CGPA required?</div>
            <div className="wiz-hint">Candidates with a CGPA below this threshold will be automatically rejected.</div>
            <div className="wiz-big-number">
              <button className="wiz-stepper-btn" onClick={() => set({ min_cgpa: Math.max(0, Math.round((draft.min_cgpa - 0.5) * 10) / 10) })}>−</button>
              <span className="wiz-num-display">{draft.min_cgpa.toFixed(1)}<small>/10</small></span>
              <button className="wiz-stepper-btn" onClick={() => set({ min_cgpa: Math.min(10, Math.round((draft.min_cgpa + 0.5) * 10) / 10) })}>+</button>
            </div>
            <input type="range" min="0" max="10" step="0.5" value={draft.min_cgpa}
              onChange={e => set({ min_cgpa: Number(e.target.value) })}
              className="wiz-slider" />
            <div className="wiz-range-labels"><span>0 — No minimum</span><span>10 — Perfect</span></div>
            <div className="wiz-context-pills">
              {[6.0, 6.5, 7.0, 7.5, 8.0, 8.5].map(v => (
                <button key={v} className={`wiz-suggest ${draft.min_cgpa === v ? 'active' : ''}`}
                  onClick={() => set({ min_cgpa: v })}>{v.toFixed(1)}</button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3 — Experience */}
        {step === 3 && (
          <div className="wiz-step-body">
            <div className="wiz-question">Minimum work experience required?</div>
            <div className="wiz-hint">Minimum years of professional experience a candidate must have.</div>
            <div className="wiz-big-number">
              <button className="wiz-stepper-btn" onClick={() => set({ min_experience: Math.max(0, Math.round((draft.min_experience - 0.5) * 10) / 10) })}>−</button>
              <span className="wiz-num-display">{draft.min_experience}<small>yr{draft.min_experience !== 1 ? 's' : ''}</small></span>
              <button className="wiz-stepper-btn" onClick={() => set({ min_experience: Math.min(20, Math.round((draft.min_experience + 0.5) * 10) / 10) })}>+</button>
            </div>
            <div className="wiz-context-pills">
              {[0, 0.5, 1, 1.5, 2, 3, 5].map(v => (
                <button key={v} className={`wiz-suggest ${draft.min_experience === v ? 'active' : ''}`}
                  onClick={() => set({ min_experience: v })}>{v === 0 ? 'Fresher' : `${v} yr`}</button>
              ))}
            </div>
          </div>
        )}

        {/* Step 4 — Skills */}
        {step === 4 && (
          <div className="wiz-step-body">
            <div className="wiz-question">What technical skills are required?</div>
            <div className="wiz-hint">Add skills one by one. Candidates missing mandatory skills will be rejected.</div>

            {draft.required_skills.length > 0 && (
              <div className="wiz-added-chips">
                {draft.required_skills.map(s => (
                  <span key={s} className="chip-x">
                    {s}
                    <button onClick={() => set({ required_skills: draft.required_skills.filter(x => x !== s) })}>×</button>
                  </span>
                ))}
              </div>
            )}

            <div className="wiz-input-row">
              <input ref={inputRef} type="text" value={skillInput}
                onChange={e => setSkillInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { addSkill(skillInput) } }}
                placeholder="Type a skill and press Enter…" />
              <button className="btn primary" onClick={() => addSkill(skillInput)}>+ Add</button>
            </div>

            {suggestedSkills.length > 0 && (
              <div>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 6, fontWeight: 500 }}>Quick add:</div>
                <div className="wiz-chips-row">
                  {suggestedSkills.map(s => (
                    <button key={s} className="wiz-suggest" onClick={() => addSkill(s)}>{s}</button>
                  ))}
                </div>
              </div>
            )}

            <label className="wiz-toggle-row" style={{ marginTop: 12 }}>
              <input type="checkbox" checked={draft.skills_mandatory}
                onChange={e => set({ skills_mandatory: e.target.checked })} />
              <span>Mandatory — candidates missing any skill are rejected (not just scored lower)</span>
            </label>
          </div>
        )}

        {/* Step 5 — Certifications */}
        {step === 5 && (
          <div className="wiz-step-body">
            <div className="wiz-question">Any required certifications?</div>
            <div className="wiz-hint">Add industry certifications. You can choose whether they're mandatory or just boost the score.</div>

            {draft.required_certifications.length > 0 && (
              <div className="wiz-added-chips">
                {draft.required_certifications.map(c => (
                  <span key={c} className="chip-x">
                    {c}
                    <button onClick={() => set({ required_certifications: draft.required_certifications.filter(x => x !== c) })}>×</button>
                  </span>
                ))}
              </div>
            )}

            <div className="wiz-input-row">
              <input type="text" value={certInput}
                onChange={e => setCertInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { addCert(certInput) } }}
                placeholder="Type a certification and press Enter…" />
              <button className="btn primary" onClick={() => addCert(certInput)}>+ Add</button>
            </div>

            {suggestedCerts.length > 0 && (
              <div>
                <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 6, fontWeight: 500 }}>Common certifications:</div>
                <div className="wiz-chips-row">
                  {suggestedCerts.map(c => (
                    <button key={c} className="wiz-suggest" onClick={() => addCert(c)}>{c}</button>
                  ))}
                </div>
              </div>
            )}

            {draft.required_certifications.length > 0 && (
              <label className="wiz-toggle-row" style={{ marginTop: 12 }}>
                <input type="checkbox" checked={draft.certifications_mandatory}
                  onChange={e => set({ certifications_mandatory: e.target.checked })} />
                <span>Mandatory — candidates without these certifications are rejected</span>
              </label>
            )}

            <button className="btn" style={{ marginTop: 12, fontSize: 13 }}
              onClick={() => { set({ required_certifications: [], certifications_mandatory: false }); setStep(6) }}>
              Skip — no certifications required →
            </button>
          </div>
        )}

        {/* Step 6 — Location */}
        {step === 6 && (
          <div className="wiz-step-body">
            <div className="wiz-question">Where should candidates be located?</div>
            <div className="wiz-hint">A location constraint is a hard rule — candidates from other cities are rejected.</div>

            <div className="wiz-location-options">
              <label className={`wiz-loc-card ${anyLocation ? 'active' : ''}`}>
                <input type="radio" checked={anyLocation} onChange={() => setAnyLocation(true)} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>🌍 Any Location</div>
                  <div style={{ color: 'var(--muted)', fontSize: 13, marginTop: 3 }}>Remote-friendly or location not a factor</div>
                </div>
              </label>
              <label className={`wiz-loc-card ${!anyLocation ? 'active' : ''}`}>
                <input type="radio" checked={!anyLocation} onChange={() => setAnyLocation(false)} />
                <div>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>📍 Specific City</div>
                  <div style={{ color: 'var(--muted)', fontSize: 13, marginTop: 3 }}>Only candidates from this city will pass</div>
                </div>
              </label>
            </div>

            {!anyLocation && (
              <div style={{ marginTop: 16 }}>
                <input type="text" value={draft.location ?? ''} placeholder="Enter city, e.g. Bengaluru"
                  onChange={e => set({ location: e.target.value || null })}
                  style={{ fontSize: 16, padding: '12px 16px' }} />
                {(options?.locations ?? []).length > 0 && (
                  <div className="wiz-chips-row" style={{ marginTop: 10 }}>
                    {options!.locations.map(l => (
                      <button key={l} className={`wiz-suggest ${draft.location === l ? 'active' : ''}`}
                        onClick={() => set({ location: l })}>{l}</button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Step 7 — Openings & Thresholds */}
        {step === 7 && (
          <div className="wiz-step-body">
            <div className="wiz-question">How many positions and scoring thresholds?</div>
            <div className="wiz-hint">Set the number of openings and the minimum scores to shortlist or wait-list a candidate.</div>

            <div className="wiz-threshold-grid">
              <div className="wiz-th-block">
                <div className="wiz-th-label">Number of Openings</div>
                <div className="wiz-big-number" style={{ marginTop: 8 }}>
                  <button className="wiz-stepper-btn" onClick={() => set({ openings: Math.max(1, draft.openings - 1) })}>−</button>
                  <span className="wiz-num-display">{draft.openings}<small>position{draft.openings !== 1 ? 's' : ''}</small></span>
                  <button className="wiz-stepper-btn" onClick={() => set({ openings: Math.min(50, draft.openings + 1) })}>+</button>
                </div>
              </div>

              <div className="wiz-th-block">
                <div className="wiz-th-label" style={{ color: 'var(--pass)' }}>✅ Shortlist Threshold</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 8 }}>
                  <span style={{ fontSize: 32, fontWeight: 700, color: 'var(--pass)' }}>{draft.thresholds.selected}</span>
                  <input type="range" min={draft.thresholds.waitlist} max="100" step="5"
                    value={draft.thresholds.selected}
                    onChange={e => set({ thresholds: { ...draft.thresholds, selected: Number(e.target.value) } })}
                    className="wiz-slider" style={{ flex: 1 }} />
                  <span style={{ color: 'var(--muted)', fontSize: 13 }}>/ 100</span>
                </div>
                <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>Score ≥ {draft.thresholds.selected} → Shortlisted</div>
              </div>

              <div className="wiz-th-block">
                <div className="wiz-th-label" style={{ color: 'var(--warn)' }}>⏳ Wait List Threshold</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 8 }}>
                  <span style={{ fontSize: 32, fontWeight: 700, color: 'var(--warn)' }}>{draft.thresholds.waitlist}</span>
                  <input type="range" min="0" max={draft.thresholds.selected} step="5"
                    value={draft.thresholds.waitlist}
                    onChange={e => set({ thresholds: { ...draft.thresholds, waitlist: Number(e.target.value) } })}
                    className="wiz-slider" style={{ flex: 1 }} />
                  <span style={{ color: 'var(--muted)', fontSize: 13 }}>/ 100</span>
                </div>
                <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>Score ≥ {draft.thresholds.waitlist} and &lt; {draft.thresholds.selected} → Wait List</div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="wiz-nav">
          {step > 0
            ? <button className="btn" onClick={() => setStep(s => s - 1)}>← Back</button>
            : <div />}

          <div style={{ display: 'flex', gap: 10 }}>
            {step < STEPS.length - 1 ? (
              <button className="btn primary lg" disabled={!canNext()} onClick={() => setStep(s => s + 1)}>
                Next →
              </button>
            ) : (
              <button className="btn primary lg" disabled={saving || !canNext()} onClick={finish}>
                {saving ? 'Saving…' : '✓ Save & Upload Resumes'}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Summary panel */}
      <div className="wiz-summary">
        <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 12, color: 'var(--ink)' }}>Summary</div>
        {[
          { label: 'Role', value: draft.title || '—' },
          { label: 'Degree', value: draft.required_degrees.join(', ') || '—' },
          { label: 'Min CGPA', value: draft.min_cgpa.toFixed(1) },
          { label: 'Experience', value: `${draft.min_experience} yr` },
          { label: 'Skills', value: draft.required_skills.length > 0 ? draft.required_skills.join(', ') : '—' },
          { label: 'Certs', value: draft.required_certifications.length > 0 ? draft.required_certifications.join(', ') : 'None' },
          { label: 'Location', value: anyLocation ? 'Any' : (draft.location ?? 'Any') },
          { label: 'Openings', value: String(draft.openings) },
        ].map(r => (
          <div key={r.label} className="wiz-sum-row">
            <span className="wiz-sum-label">{r.label}</span>
            <span className="wiz-sum-val">{r.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
