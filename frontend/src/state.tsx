import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, ApiError, setUnauthorizedHandler, type User } from './api'
import type { Candidate, Job, RunResult, SampleResult, WorkflowStage } from './types'

interface AppState {
  user: User | null
  authChecked: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (name: string, email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  job: Job | null
  candidates: Candidate[]
  run: RunResult | null
  running: boolean
  error: string | null
  setError: (e: string | null) => void
  refresh: () => Promise<void>
  setJob: (j: Job) => void
  runPipeline: () => Promise<RunResult | null>
  loadSamples: () => Promise<SampleResult | null>
  stage: WorkflowStage              // progress of THIS visit: ticks only appear as steps are completed
  setStage: (s: WorkflowStage) => void
  resetProgress: () => void
}

const Ctx = createContext<AppState>(null as unknown as AppState)
export const useApp = () => useContext(Ctx)

export function AppProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [authChecked, setAuthChecked] = useState(false)
  const [job, setJob] = useState<Job | null>(null)
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [run, setRun] = useState<RunResult | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stage, setStage] = useState<WorkflowStage>('idle')
  const resetProgress = useCallback(() => setStage('idle'), [])

  const clearData = () => { setJob(null); setCandidates([]); setRun(null); setError(null); setStage('idle') }

  const refresh = useCallback(async () => {
    try {
      const [j, c, r] = await Promise.all([api.getJob(), api.candidates(), api.latestRun()])
      setJob(j); setCandidates(c); setRun(r); setError(null)
    } catch (e) {
      if (!(e instanceof ApiError && e.status === 401)) setError(e instanceof ApiError ? e.message : String(e))
    }
  }, [])

  // If any request comes back "not signed in" (session expired / signed out elsewhere) show the login page.
  useEffect(() => { setUnauthorizedHandler(() => { setUser(null); clearData() }) }, [])

  useEffect(() => {
    api.me().then(u => { setUser(u); return refresh() }).catch(() => setUser(null)).finally(() => setAuthChecked(true))
  }, [refresh])

  const signIn = useCallback(async (email: string, password: string) => {
    const u = await api.login(email, password)   // errors are shown by the login form
    clearData(); setUser(u); await refresh()
  }, [refresh])

  const signUp = useCallback(async (name: string, email: string, password: string) => {
    const u = await api.register(name, email, password)
    clearData(); setUser(u); await refresh()
  }, [refresh])

  const signOut = useCallback(async () => {
    try { await api.logout() } finally { setUser(null); clearData() }
  }, [])

  const runPipeline = useCallback(async () => {
    setRunning(true)
    try {
      const r = await api.run()
      setRun(r); setError(null)
      return r
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e))
      return null
    } finally {
      setRunning(false)
    }
  }, [])

  const loadSamples = useCallback(async () => {
    try {
      const r = await api.loadSamples()
      await refresh()
      setStage('idle')
      return r
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e))
      return null
    }
  }, [refresh])

  return (
    <Ctx.Provider value={{ user, authChecked, signIn, signUp, signOut, job, candidates, run, running, error, setError, refresh, setJob, runPipeline, loadSamples, stage, setStage, resetProgress }}>
      {children}
    </Ctx.Provider>
  )
}
