import { useEffect, useState } from 'react'
import { Navigate, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { Icon } from './components/icons'
import { ErrorBanner } from './components/ui'
import { Stepper, STEPS, stepOf, useWorkflow } from './components/workflow'
import Dashboard from './pages/Dashboard'
import JobPage from './pages/JobPage'
import UploadPage from './pages/UploadPage'
import PipelinePage from './pages/PipelinePage'
import ResultsPage from './pages/ResultsPage'
import CandidateDetail from './pages/CandidateDetail'
import VisualizationPage from './pages/VisualizationPage'
import RankingPage from './pages/RankingPage'
import AlgorithmsPage from './pages/AlgorithmsPage'
import AuthPage from './pages/AuthPage'
import WizardPage from './pages/WizardPage'
import HistoryPage from './pages/HistoryPage'
import LiveReviewPage from './pages/LiveReviewPage'
import ChatBot from './components/ChatBot'
import { useApp } from './state'

function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const q = new URLSearchParams(window.location.search).get('theme')
    if (q === 'light' || q === 'dark') return q
    try { const s = localStorage.getItem('theme'); if (s === 'light' || s === 'dark') return s } catch { /* storage blocked */ }
    return 'light'
  })
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('theme', theme) } catch { /* ignore */ }
  }, [theme])
  return [theme, () => setTheme(t => (t === 'dark' ? 'light' : 'dark'))] as const
}

export default function App() {
  const [theme, toggle] = useTheme()
  const { pathname } = useLocation()
  const wf = useWorkflow()
  const { user, authChecked, signOut, job } = useApp()
  const onReview = stepOf(pathname) === 4

  if (!authChecked) return <div className="auth-loading">Loading…</div>
  if (!user) return <AuthPage />

  return (
    <div className="app">
      <aside className="sidebar">
        {/* Brand */}
        <div className="brand">
          <div className="logo"><Icon name="users" /></div>
          <div><b>TalentFlow AI</b><small>AI-Powered Recruitment</small></div>
        </div>

        {/* Primary tabs — at the top */}
        <div className="primary-tabs">
          <NavLink to="/wizard" className={({ isActive }) => `pt-link new-rec ${isActive ? 'active' : ''}`}>
            <div className="pt-icon"><Icon name="play" /></div>
            <div className="pt-text">
              <span className="pt-label">New Recruitment</span>
              <span className="pt-sub">Start AI screening</span>
            </div>
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => `pt-link hist-btn ${isActive ? 'active' : ''}`}>
            <div className="pt-icon"><Icon name="file" /></div>
            <div className="pt-text">
              <span className="pt-label">History</span>
              <span className="pt-sub">Past sessions</span>
            </div>
          </NavLink>
        </div>

        {/* Active role pill */}
        {job && (
          <div className="role-pill">
            <div className="rp-label">Hiring for</div>
            <div className="rp-title">{job.title}</div>
            <div className="rp-sub">{job.location ?? 'Any location'} · {job.openings} opening{job.openings !== 1 ? 's' : ''}</div>
          </div>
        )}

        <div className="nav-label">Screening Steps</div>
        <nav className="nav">
          {STEPS.map(s => (
            <NavLink key={s.no} to={s.path} className={({ isActive }) => `${isActive || (s.no === 4 && onReview) ? 'active' : ''} ${wf.done[s.no] ? 'done' : ''}`}>
              <span className="step-no">{wf.done[s.no] ? <Icon name="check" className="" /> : s.no}</span>
              <span>{s.nav}</span>
            </NavLink>
          ))}
        </nav>

        {wf.hasRun && <>
          <div className="nav-label">Decisions</div>
          <nav className="nav">
            <NavLink to="/results" className={({ isActive }) => (isActive || pathname.startsWith('/candidates') ? 'active' : '')}>
              <Icon name="users" /><span>All Candidates</span>
            </NavLink>
            <NavLink to="/ranking" className={({ isActive }) => (isActive ? 'active' : '')}>
              <Icon name="trophy" /><span>Shortlist</span>
            </NavLink>
          </nav>
        </>}

        <div className="nav-label">Analytics</div>
        <nav className="nav">
          <NavLink to="/overview" className={({ isActive }) => (isActive ? 'active' : '')}>
            <Icon name="dashboard" /><span>Dashboard</span>
          </NavLink>
          <NavLink to="/visualize" className={({ isActive }) => (isActive ? 'active' : '')}>
            <Icon name="activity" /><span>AI Reasoning</span>
          </NavLink>
          <NavLink to="/algorithms" className={({ isActive }) => (isActive ? 'active' : '')}>
            <Icon name="book" /><span>How It Works</span>
          </NavLink>
        </nav>

        <div className="side-foot">
          <div className="whoami">
            <span className="avatar sm">{user.name.split(/\s+/).slice(0, 2).map(w => w[0]).join('').toUpperCase()}</span>
            <span><b>{user.name}</b><small>{user.email}</small></span>
          </div>
          <button className="theme-btn" onClick={signOut}><Icon name="x" /><span>Sign out</span></button>
          <button className="theme-btn" onClick={toggle} aria-label="Toggle dark mode">
            <Icon name={theme === 'dark' ? 'sun' : 'moon'} /><span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
          </button>
        </div>
      </aside>

      <main className="main">
        <ErrorBanner />
        <Stepper />
        <ChatBot />
        <Routes>
          <Route path="/" element={<Navigate to="/overview" replace />} />
          <Route path="/overview" element={<Dashboard />} />
          <Route path="/job" element={<JobPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/pipeline" element={<PipelinePage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/candidates/:id" element={<CandidateDetail />} />
          <Route path="/visualize" element={<VisualizationPage />} />
          <Route path="/ranking" element={<RankingPage />} />
          <Route path="/algorithms" element={<AlgorithmsPage />} />
          <Route path="/wizard" element={<WizardPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/live-review" element={<LiveReviewPage />} />
        </Routes>
      </main>
    </div>
  )
}
