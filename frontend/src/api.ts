import type { AlgoInfo, Candidate, HistoryDetail, HistoryEntry, JdSuggestion, Job, JobOptions, RunResult, SampleResult, UploadResult } from './types'

export class ApiError extends Error {
  details: string[]
  status: number
  constructor(message: string, details: string[] = [], status = 0) {
    super(message)
    this.details = details.length ? details : [message]
    this.status = status
  }
}

// Called when the server says "not signed in" (e.g. the session expired) so the app can show the login page.
let onUnauthorized: () => void = () => {}
export const setUnauthorizedHandler = (fn: () => void) => { onUnauthorized = fn }

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(url, init)
  } catch {
    throw new ApiError('Cannot reach the backend. Is it running on http://127.0.0.1:8000 ?')
  }
  if (!res.ok) {
    let detail: unknown = res.statusText
    try { detail = (await res.json()).detail } catch { /* not JSON */ }
    const list = Array.isArray(detail) ? detail.map(String) : [String(detail)]
    if (res.status === 401 && !url.startsWith('/api/auth/')) onUnauthorized()
    throw new ApiError(list[0], list, res.status)
  }
  return res.json() as Promise<T>
}

const json = (method: string, body: unknown): RequestInit => ({
  method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
})

export interface User { id: number; name: string; email: string }

export const api = {
  me: () => request<User>('/api/auth/me'),
  login: (email: string, password: string) => request<User>('/api/auth/login', json('POST', { email, password })),
  register: (name: string, email: string, password: string) => request<User>('/api/auth/register', json('POST', { name, email, password })),
  logout: () => request<unknown>('/api/auth/logout', { method: 'POST' }),
  getJob: () => request<Job>('/api/job'),
  options: () => request<JobOptions>('/api/options'),
  parseJd: (text: string) => request<JdSuggestion>('/api/job/parse', json('POST', { text })),
  saveJob: (job: Job) => request<Job>('/api/job', json('PUT', job)),
  candidates: () => request<Candidate[]>('/api/candidates'),
  upload: (files: File[]) => {
    const form = new FormData()
    files.forEach(f => form.append('files', f))
    return request<{ results: UploadResult[] }>('/api/resumes', { method: 'POST', body: form })
  },
  editCandidate: (id: number, patch: Partial<Candidate>) => request<Candidate>(`/api/candidates/${id}`, json('PUT', patch)),
  deleteCandidate: (id: number) => request<unknown>(`/api/candidates/${id}`, { method: 'DELETE' }),
  clearCandidates: () => request<unknown>('/api/candidates', { method: 'DELETE' }),
  loadSamples: () => request<SampleResult>('/api/samples/load', { method: 'POST' }),
  run: () => request<RunResult>('/api/run', { method: 'POST' }),
  latestRun: () => request<RunResult | null>('/api/run/latest'),
  algorithms: () => request<AlgoInfo>('/api/algorithms'),
  chat: (message: string) => request<{ reply: string }>('/api/chat', json('POST', { message })),
  history: () => request<HistoryEntry[]>('/api/history'),
  getHistoryDetail: (id: number) => request<HistoryDetail>(`/api/history/${id}`),
  deleteHistory: (id: number) => request<unknown>(`/api/history/${id}`, { method: 'DELETE' }),
  reopenHistory: (id: number) => request<Job>(`/api/history/${id}/reopen`, { method: 'POST' }),
}
