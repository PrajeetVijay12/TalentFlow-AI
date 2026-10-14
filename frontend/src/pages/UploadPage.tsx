import { Fragment, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api'
import { Card, Empty, PageHead } from '../components/ui'
import { PageFoot } from '../components/workflow'
import { Icon } from '../components/icons'
import { useApp } from '../state'
import type { Candidate, UploadResult } from '../types'

export default function UploadPage() {
  const { candidates, refresh, loadSamples, setError, resetProgress } = useApp()
  const [results, setResults] = useState<UploadResult[]>([])
  const [sampleMsg, setSampleMsg] = useState<{ ok: boolean; text: string } | null>(null)
  const [busy, setBusy] = useState(false); const [over, setOver] = useState(false)
  const [editing, setEditing] = useState<number | null>(null)
  const nav = useNavigate()
  const { job } = useApp()
  const input = useRef<HTMLInputElement>(null)

  const [loadingDemo, setLoadingDemo] = useState(false)
  async function loadDemo() {
    setLoadingDemo(true); setSampleMsg(null)
    const r = await loadSamples()
    setLoadingDemo(false)
    if (!r) return
    setResults(r.results)
    setSampleMsg(r.added > 0
      ? { ok: true, text: `Added ${r.added} sample resume${r.added > 1 ? 's' : ''}${r.already_loaded ? ` (${r.already_loaded} were already in your list)` : ''}.${r.sample_job_applied ? ' The sample job requirements were applied too.' : ' Your own saved job requirements were kept.'}` }
      : { ok: false, text: `The ${r.already_loaded} sample resumes are already in your list below — nothing new to add. Press “Clear all” first if you want to start over.` })
  }

  async function send(files: File[]) {
    if (!files.length) { setError('No resumes selected. Choose at least one PDF or DOCX file.'); return }
    setBusy(true)
    try { setResults((await api.upload(files)).results); setSampleMsg(null); resetProgress(); await refresh() }
    catch (e) { setError(e instanceof ApiError ? e.message : String(e)) }
    finally { setBusy(false); if (input.current) input.current.value = '' }
  }

  return (
    <>
      <PageHead eyebrow="Step 1 of 4" title="Resume Upload" desc="PDF and DOCX files, up to 5 MB each. Files are parsed locally with rule-based extraction — nothing is sent to any external service."
        actions={<>
          <button className="btn" onClick={loadDemo} disabled={loadingDemo}>{loadingDemo ? 'Loading…' : 'Load sample data'}</button>
          {candidates.length > 0 && <button className="btn danger" onClick={async () => { await api.clearCandidates(); setResults([]); setSampleMsg(null); resetProgress(); await refresh() }}>Clear all</button>}
        </>} />

      <div className={`drop ${over ? 'over' : ''}`}
        onDragOver={e => { e.preventDefault(); setOver(true) }} onDragLeave={() => setOver(false)}
        onDrop={e => { e.preventDefault(); setOver(false); void send([...e.dataTransfer.files]) }}>
        <div className="big-ico"><Icon name="upload" /></div>
        <h3 style={{ justifyContent: 'center' }}>Drag & drop resumes here</h3>
        <p className="muted">or</p>
        <input ref={input} type="file" multiple accept=".pdf,.docx" hidden onChange={e => void send([...(e.target.files ?? [])])} />
        <button className="btn primary" disabled={busy} onClick={() => input.current?.click()}>{busy ? 'Parsing…' : 'Choose files'}</button>
      </div>

      {sampleMsg && <div className={`alert ${sampleMsg.ok ? 'ok' : 'info'}`} role="status" style={{ marginTop: 16 }}>{sampleMsg.text}</div>}

      {results.length > 0 && (
        <Card title="Upload report" sub="What happened to each file you just sent">
          <table><tbody>{results.map((r, i) => (
            <tr key={i}><td className="mono">{r.filename}</td>
              <td><span className={`badge ${r.status === 'ok' ? 'b-pass' : r.status === 'duplicate' ? 'b-wait' : 'b-fail'}`}>{r.status.toUpperCase()}</span></td>
              <td>{r.message}</td></tr>))}</tbody></table>
        </Card>
      )}

      <div style={{ height: 16 }} />
      {candidates.length === 0 ? <Empty title="No resumes yet">Upload some resumes, or click “Load sample data” to try the 7 bundled candidates.</Empty> : (
        <Card title={`Parsed candidates (${candidates.length})`} sub="Structured data extracted from each resume. Review it — you can correct any field before running the pipeline.">
          <div className="table-wrap"><table>
            <thead><tr><th>Name</th><th>Degree · CGPA</th><th>Skills</th><th className="num">Exp (yr)</th><th>Projects</th><th>Certs</th><th>Location</th><th /></tr></thead>
            <tbody>{candidates.map(c => (
              <Fragment key={c.id}>
                <tr>
                  <td><b>{c.name}</b><div className="small muted">{c.email ?? 'no email'}<br />{c.phone ?? 'no phone'}</div>
                    {c.missing_fields.length > 0 && <span className="badge b-wait" title="Fields not found in the resume">missing: {c.missing_fields.join(', ')}</span>}</td>
                  <td>{c.degree ?? <span className="muted">—</span>} · {c.cgpa ?? '—'}</td>
                  <td>{c.skills.map(s => <span key={s} className="chip">{s}</span>)}</td>
                  <td className="num">{c.experience}</td>
                  <td>{c.projects.map(p => <div key={p.name} className="small">{p.name} <span className="badge b-info">{p.score}</span></div>)}</td>
                  <td>{c.certifications.map(s => <span key={s} className="chip">{s}</span>)}</td>
                  <td>{c.location ?? '—'}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <button className="btn sm" onClick={() => setEditing(editing === c.id ? null : c.id)}>Edit</button>{' '}
                    <button className="btn sm danger" onClick={async () => { await api.deleteCandidate(c.id); resetProgress(); await refresh() }}>Remove</button></td>
                </tr>
                {editing === c.id && <tr><td colSpan={8}><EditRow cand={c} done={async () => { setEditing(null); await refresh() }} /></td></tr>}
              </Fragment>))}</tbody>
          </table></div>
        </Card>
      )}
      <PageFoot hint={candidates.length
        ? <>{candidates.length} resume(s) ready. The workflow will screen them for <b>{job?.title ?? 'the role'}</b> using your saved job requirements.</>
        : 'Add at least one resume, then start the workflow.'}>
        <Link className="btn" to="/job">Review job requirements</Link>
        <button className="btn primary lg" disabled={!candidates.length} onClick={() => nav('/pipeline', { state: { autorun: true } })}>
          <Icon name="play" />Start workflow</button>
      </PageFoot>
    </>
  )
}

function EditRow({ cand, done }: { cand: Candidate; done: () => void }) {
  const { setError } = useApp()
  const [degree, setDegree] = useState(cand.degree ?? ''); const [cgpa, setCgpa] = useState(String(cand.cgpa ?? ''))
  const [exp, setExp] = useState(String(cand.experience)); const [loc, setLoc] = useState(cand.location ?? '')
  const [skills, setSkills] = useState(cand.skills.join(', '))
  async function save() {
    try {
      await api.editCandidate(cand.id, { degree: degree || null, cgpa: cgpa === '' ? null : Number(cgpa), experience: Number(exp) || 0,
        location: loc || null, skills: skills.split(',').map(s => s.trim()).filter(Boolean) })
      done()
    } catch (e) { setError(e instanceof ApiError ? e.message : String(e)) }
  }
  return (
    <div className="card" style={{ background: '#fafaff' }}>
      <div className="grid g4" style={{ gap: 12 }}>
        <label className="field">Degree<input type="text" value={degree} onChange={e => setDegree(e.target.value)} /></label>
        <label className="field">CGPA<input type="text" value={cgpa} onChange={e => setCgpa(e.target.value)} /></label>
        <label className="field">Experience (yr)<input type="text" value={exp} onChange={e => setExp(e.target.value)} /></label>
        <label className="field">Location<input type="text" value={loc} onChange={e => setLoc(e.target.value)} /></label>
      </div>
      <label className="field" style={{ marginTop: 10 }}>Skills (comma separated)<input type="text" value={skills} onChange={e => setSkills(e.target.value)} /></label>
      <div className="small muted" style={{ marginTop: 10 }}><b>How it was extracted:</b> {cand.notes.join(' ') || '—'}</div>
      <div style={{ marginTop: 10 }} className="row"><button className="btn primary sm" onClick={save}>Save changes</button></div>
    </div>
  )
}
