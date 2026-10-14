import { useState, type FormEvent } from 'react'
import { ApiError } from '../api'
import { Icon } from '../components/icons'
import { useApp } from '../state'

export default function AuthPage() {
  const { signIn, signUp } = useApp()
  const [mode, setMode] = useState<'in' | 'up'>('in')
  const [name, setName] = useState(''); const [email, setEmail] = useState('')
  const [password, setPassword] = useState(''); const [confirm, setConfirm] = useState('')
  const [show, setShow] = useState(false); const [busy, setBusy] = useState(false)
  const [errors, setErrors] = useState<string[]>([])

  const switchTo = (m: 'in' | 'up') => { setMode(m); setErrors([]); setPassword(''); setConfirm('') }

  async function submit(e: FormEvent) {
    e.preventDefault()
    setErrors([])
    if (mode === 'up' && password !== confirm) { setErrors(['The two passwords do not match.']); return }
    setBusy(true)
    try {
      if (mode === 'in') await signIn(email.trim(), password)
      else await signUp(name.trim(), email.trim(), password)
    } catch (err) {
      setErrors(err instanceof ApiError ? err.details : ['Something went wrong. Please try again.'])
    } finally { setBusy(false) }
  }

  return (
    <div className="auth-wrap">
      <aside className="auth-side">
        <div className="brand"><div className="logo"><Icon name="users" /></div><div><b>TalentFlow AI</b><small>AI-Powered Recruitment</small></div></div>
        <div>
          <h1>Screen resumes with decisions you can explain.</h1>
          <ul className="auth-points">
            <li><Icon name="check" /><span><b>Rule-based, not a black box.</b> BFS/DFS, CSP, Alpha-Beta — every score has a traceable reason.</span></li>
            <li><Icon name="shield" /><span><b>Your candidates stay private.</b> Resumes are processed on this server and each account sees only its own data.</span></li>
            <li><Icon name="list" /><span><b>AI chatbot included.</b> Ask "Why was X rejected?" and get a full logical reasoning trace.</span></li>
          </ul>
        </div>
        <small className="auth-foot">Classical AI project · no machine learning</small>
      </aside>

      <main className="auth-main">
        <form className="auth-card" onSubmit={submit} noValidate>
          <h2>{mode === 'in' ? 'Welcome back' : 'Create your account'}</h2>
          <p className="muted">{mode === 'in' ? 'Sign in to continue screening candidates.' : 'It takes a few seconds. You can start screening right away.'}</p>

          {errors.length > 0 && <div className="alert err" role="alert"><div>{errors.length === 1 ? errors[0] : <ul>{errors.map((m, i) => <li key={i}>{m}</li>)}</ul>}</div></div>}

          {mode === 'up' && (
            <label className="field">Full name
              <input type="text" autoComplete="name" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Asha Kumar" autoFocus /></label>)}
          <label className="field">Email
            <input type="text" inputMode="email" autoComplete="username" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" autoFocus={mode === 'in'} /></label>
          <label className="field">
            <span className="row" style={{ justifyContent: 'space-between' }}>Password
              <button type="button" className="link-btn" onClick={() => setShow(s => !s)}>{show ? 'Hide' : 'Show'}</button></span>
            <input type={show ? 'text' : 'password'} autoComplete={mode === 'in' ? 'current-password' : 'new-password'} value={password}
              onChange={e => setPassword(e.target.value)} placeholder={mode === 'up' ? 'At least 8 characters' : 'Your password'} />
          </label>
          {mode === 'up' && (
            <label className="field">Confirm password
              <input type={show ? 'text' : 'password'} autoComplete="new-password" value={confirm} onChange={e => setConfirm(e.target.value)} /></label>)}

          <button className="btn primary lg" type="submit" disabled={busy || !email || !password || (mode === 'up' && !name)} style={{ width: '100%', justifyContent: 'center' }}>
            {busy ? 'Please wait…' : mode === 'in' ? 'Sign in' : 'Create account'}</button>

          <p className="auth-switch">
            {mode === 'in' ? <>New here? <button type="button" className="link-btn" onClick={() => switchTo('up')}>Create an account</button></>
              : <>Already have an account? <button type="button" className="link-btn" onClick={() => switchTo('in')}>Sign in</button></>}
          </p>
        </form>
      </main>
    </div>
  )
}
