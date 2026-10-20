/**
 * Generates a self-contained, print-ready HTML report for one candidate.
 * No external dependencies — the HTML embeds all styles inline so it renders
 * correctly when saved or printed as PDF.
 */
import type { CandidateResult, Job } from '../types'

const STATUS_COLOR: Record<string, string> = {
  Selected: '#16a34a',
  'Wait List': '#d97706',
  Rejected: '#dc2626',
}

function badge(text: string, color: string) {
  return `<span style="display:inline-block;padding:2px 10px;border-radius:12px;background:${color}20;color:${color};font-size:12px;font-weight:600;border:1px solid ${color}40">${text}</span>`
}

function passOrFail(ok: boolean) {
  return ok ? badge('PASS', '#16a34a') : badge('FAIL', '#dc2626')
}

function row(label: string, value: string) {
  return `<tr><td style="color:#6b7280;padding:6px 12px 6px 0;white-space:nowrap;vertical-align:top">${label}</td><td style="padding:6px 0;font-weight:500">${value}</td></tr>`
}

function section(title: string, body: string) {
  return `
    <div style="margin-bottom:24px">
      <h3 style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;margin:0 0 10px;padding-bottom:6px;border-bottom:1px solid #e5e7eb">${title}</h3>
      ${body}
    </div>`
}

function table(headers: string[], rows: string[][], highlight: (r: string[]) => string = () => '') {
  const ths = headers.map(h => `<th style="text-align:left;padding:6px 10px;font-size:12px;color:#6b7280;font-weight:600;border-bottom:2px solid #e5e7eb">${h}</th>`).join('')
  const trs = rows.map(r => {
    const bg = highlight(r)
    const tds = r.map(c => `<td style="padding:6px 10px;border-bottom:1px solid #f3f4f6;font-size:13px;${bg}">${c}</td>`).join('')
    return `<tr>${tds}</tr>`
  }).join('')
  return `<table style="width:100%;border-collapse:collapse;font-size:13px"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`
}

export function generateCandidateReport(c: CandidateResult, job: Job, runDate: string): string {
  const p = c.profile
  const h = c.heuristic
  const fc = c.forward_chaining
  const bc = c.backward_chaining
  const res = c.resolution
  const statusColor = STATUS_COLOR[c.final.status] ?? '#6b7280'

  // ── Profile ──────────────────────────────────────────────────────────────
  const profileBody = `<table>${[
    row('Degree · CGPA', `${p.degree ?? '—'} · ${p.cgpa ?? '—'}`),
    row('Experience', `${p.experience} year(s)`),
    row('Location', p.location ?? '—'),
    row('Skills', p.skills.length ? p.skills.map(s => `<span style="background:#eff6ff;color:#1d4ed8;padding:1px 8px;border-radius:10px;font-size:12px;margin:2px;display:inline-block">${s}</span>`).join('') : '—'),
    row('Certifications', p.certifications.length ? p.certifications.join(', ') : '—'),
    row('Projects', p.projects.length ? p.projects.map(x => `${x.name} <em style="color:#6b7280">(${x.category.replace('_', ' ')}, score ${x.score})</em>`).join('<br>') : '—'),
    row('Email', p.email ?? '—'),
    row('Phone', p.phone ?? '—'),
    row('Source file', `<code style="font-size:12px">${p.filename}</code>`),
  ].join('')}</table>`

  // ── Decision ─────────────────────────────────────────────────────────────
  const decisionBody = `
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:12px">
      <div style="width:72px;height:72px;border-radius:50%;background:${statusColor}15;border:3px solid ${statusColor};display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:800;color:${statusColor}">${c.final.score !== null ? c.final.score.toFixed(0) : '—'}</div>
      <div>
        <div style="font-size:18px;font-weight:700;color:${statusColor}">${c.final.status}</div>
        <div style="color:#6b7280;font-size:13px">Rank #${c.final.rank} of ${c.final.rank} candidates</div>
      </div>
    </div>
    <ul style="margin:0;padding-left:18px;color:#374151;line-height:1.7">
      ${c.final.reasons.map(r => `<li style="font-size:13px">${r}</li>`).join('')}
    </ul>`

  // ── Pipeline verdicts ─────────────────────────────────────────────────────
  const verdictBody = table(
    ['Stage', 'Algorithm', 'Result'],
    [
      ['BFS / DFS Eligibility', 'Uninformed search over criteria tree', c.eligibility.eligible ? badge('ELIGIBLE', '#16a34a') : badge('INELIGIBLE', '#dc2626')],
      ['A* Eligibility', 'Informed search — f(n)=g(n)+h(n)', c.eligibility.astar ? (c.eligibility.astar.eligible ? badge('ELIGIBLE', '#16a34a') : badge('INELIGIBLE', '#dc2626')) : '—'],
      ['Heuristic Score', 'Best-first weighted scoring', h ? `<b>${h.total} / 100</b>` : '—'],
      ['CSP', 'Constraint satisfaction', c.csp.valid ? badge('VALID', '#16a34a') : badge('VIOLATED', '#dc2626')],
      ['Forward Chaining', 'Data-driven inference', fc.goal_reached ? badge('ELIGIBLE', '#16a34a') : badge('NOT ELIGIBLE', '#dc2626')],
      ['Backward Chaining', 'Goal-driven proof', bc.proven ? badge('PROVEN', '#16a34a') : badge('NOT PROVEN', '#dc2626')],
      ['Resolution', 'Refutation (CNF)', res ? (res.proven ? badge('PROVEN', '#16a34a') : badge('NOT PROVEN', '#dc2626')) : '—'],
      ['Alpha-Beta Pruning', 'Minimax game tree', badge(c.alpha_beta.selected ? 'SELECTED' : c.alpha_beta.status.startsWith('Searched') ? 'SEARCHED' : 'PRUNED', c.alpha_beta.selected ? '#16a34a' : '#6b7280')],
    ]
  )

  // ── Eligibility checks ───────────────────────────────────────────────────
  const eligBody = table(
    ['Criterion', 'Required', 'Candidate', 'BFS', 'DFS'],
    c.eligibility.bfs.checks.map(k => {
      const dfsCheck = c.eligibility.dfs.checks.find(d => d.id === k.id)
      return [
        `<b>${k.label}</b>`,
        k.required ?? '—',
        k.actual ?? '—',
        passOrFail(k.status === 'PASS'),
        dfsCheck ? passOrFail(dfsCheck.status === 'PASS') : '<span style="color:#6b7280">skipped</span>',
      ]
    })
  )

  // ── Heuristic breakdown ──────────────────────────────────────────────────
  const heuristicBody = h ? table(
    ['Component', 'Score', 'Weight', 'Contribution'],
    [
      ['Skills' + (h.parts.skills.missing.length ? ` <em style="color:#dc2626;font-size:11px">missing: ${h.parts.skills.missing.join(', ')}</em>` : ''),
        String(h.parts.skills.score), `${(h.parts.skills.weight * 100).toFixed(0)}%`, `<b>${h.parts.skills.weighted}</b>`],
      [`Experience (${h.parts.experience.candidate} / ${h.parts.experience.required} yr)`,
        String(h.parts.experience.score), `${(h.parts.experience.weight * 100).toFixed(0)}%`, `<b>${h.parts.experience.weighted}</b>`],
      [`Projects (${h.parts.projects.best_project ?? 'none'})`,
        String(h.parts.projects.score), `${(h.parts.projects.weight * 100).toFixed(0)}%`, `<b>${h.parts.projects.weighted}</b>`],
      [`Certifications` + (h.parts.certifications.missing.length ? ` <em style="color:#dc2626;font-size:11px">missing: ${h.parts.certifications.missing.join(', ')}</em>` : ''),
        String(h.parts.certifications.score), `${(h.parts.certifications.weight * 100).toFixed(0)}%`, `<b>${h.parts.certifications.weighted}</b>`],
      [`<b>Total</b>`, '', '', `<b>${h.total}</b>`],
    ]
  ) : '<div style="color:#6b7280">Not scored — candidate did not pass eligibility.</div>'

  // ── CSP constraints ──────────────────────────────────────────────────────
  const cspBody = table(
    ['Constraint', 'Rule', 'Candidate value', 'Type', 'Result'],
    c.csp.constraints.map(k => [
      `<b>${k.name}</b>`,
      `<code style="font-size:11px">${k.constraint}</code>`,
      k.candidate_value,
      k.hard ? 'hard' : 'soft',
      passOrFail(k.status === 'PASS'),
    ])
  )

  // ── Forward chaining ─────────────────────────────────────────────────────
  const fcFired = fc.fired.map(f =>
    `<tr><td style="padding:4px 8px;font-size:12px;color:#6b7280">Round ${f.round}</td><td style="padding:4px 8px;font-size:12px"><b>${f.derived}</b></td><td style="padding:4px 8px;font-size:12px;color:#6b7280">${f.text}</td></tr>`
  ).join('')
  const fcBody = `
    <div style="font-size:13px;margin-bottom:8px"><b>Initial facts:</b> ${fc.initial_facts.join(', ')}</div>
    <table style="width:100%;border-collapse:collapse">
      <thead><tr>
        <th style="text-align:left;padding:4px 8px;font-size:12px;color:#6b7280;border-bottom:2px solid #e5e7eb">Round</th>
        <th style="text-align:left;padding:4px 8px;font-size:12px;color:#6b7280;border-bottom:2px solid #e5e7eb">Derived</th>
        <th style="text-align:left;padding:4px 8px;font-size:12px;color:#6b7280;border-bottom:2px solid #e5e7eb">Rule</th>
      </tr></thead>
      <tbody>${fcFired || '<tr><td colspan="3" style="padding:8px;color:#6b7280">No rules fired.</td></tr>'}</tbody>
    </table>
    <div style="margin-top:8px;font-size:13px"><b>Goal reached:</b> ${passOrFail(fc.goal_reached)}</div>`

  // ── Backward chaining ────────────────────────────────────────────────────
  const bcBody = `
    <div style="font-size:13px;margin-bottom:8px"><b>Goal:</b> eligible</div>
    <div style="font-size:13px"><b>Proof steps:</b></div>
    <pre style="font-size:12px;background:#f9fafb;padding:10px;border-radius:6px;white-space:pre-wrap;margin:6px 0;max-height:200px;overflow-y:auto">${bc.steps.join('\n')}</pre>
    <div style="margin-top:8px;font-size:13px"><b>Conclusion:</b> ${bc.proven ? badge('PROVEN', '#16a34a') : badge('NOT PROVEN', '#dc2626')}${bc.failed_requirements.length ? ` <em style="color:#dc2626;font-size:12px"> — missing: ${bc.failed_requirements.join('; ')}</em>` : ''}</div>`

  // ── Resolution ───────────────────────────────────────────────────────────
  const resBody = res ? `
    <div style="font-size:13px;margin-bottom:8px">${res.initial_clauses} initial CNF clauses · ${res.total_clauses - res.initial_clauses} new clauses derived · ${res.resolution_steps.length} resolution step(s)</div>
    <div style="font-size:13px"><b>Conclusion:</b> ${res.proven ? badge('PROVEN BY REFUTATION', '#16a34a') : badge('CANNOT PROVE', '#dc2626')}</div>
    <div style="font-size:12px;color:#6b7280;margin-top:6px">${res.summary}</div>` : '<div style="color:#6b7280">No resolution data.</div>'

  // ── Alpha-Beta ────────────────────────────────────────────────────────────
  const abBody = c.perspectives ? `
    ${table(['Panel viewpoint', 'Score'], c.perspectives.map(x => [x.label, String(x.score)]))}
    <div style="font-size:13px;margin-top:8px;color:#6b7280">MIN value = worst-case across viewpoints. HR (MAX) selects the candidate whose worst case is highest.</div>
    <div style="margin-top:8px;font-size:13px"><b>Result:</b> ${c.alpha_beta.status}</div>` :
    '<div style="color:#6b7280">Not entered the game tree — eliminated by an earlier stage.</div>'

  // ── Job requirements sidebar ──────────────────────────────────────────────
  const jobSidebar = `
    <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:14px;font-size:12px;margin-bottom:20px">
      <div style="font-weight:700;margin-bottom:8px;color:#374151">Job Requirements</div>
      <table>${[
    row('Role', job.title ?? 'Software Engineer'),
    row('Degrees', job.required_degrees.join(', ')),
    row('Min CGPA', String(job.min_cgpa)),
    row('Min Exp', `${job.min_experience} yr`),
    row('Skills', job.required_skills.join(', ')),
    row('Location', job.location ?? 'Any'),
    row('Openings', String(job.openings)),
  ].join('')}</table>
    </div>`

  // ── Assemble ──────────────────────────────────────────────────────────────
  const initials = c.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()

  return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TalentFlow AI Report — ${c.name}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0 }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #111827; background: #fff; font-size: 14px; line-height: 1.5 }
  .page { max-width: 860px; margin: 0 auto; padding: 32px 24px }
  @media print {
    body { font-size: 12px }
    .page { padding: 0; max-width: 100% }
    .no-print { display: none }
    .pagebreak { page-break-before: always }
  }
</style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div style="display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:20px;border-bottom:2px solid #111827;margin-bottom:24px">
    <div>
      <div style="font-size:11px;font-weight:700;letter-spacing:.1em;color:#6b7280;text-transform:uppercase;margin-bottom:4px">TalentFlow AI — Candidate Screening Report</div>
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:6px">
        <div style="width:52px;height:52px;border-radius:50%;background:${statusColor}20;border:2px solid ${statusColor};display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:800;color:${statusColor};flex-shrink:0">${initials}</div>
        <div>
          <h1 style="font-size:22px;font-weight:800;color:#111827">${c.name}</h1>
          <div style="font-size:13px;color:#6b7280">${p.email ?? ''} · ${p.phone ?? ''} · ${p.location ?? '—'}</div>
        </div>
      </div>
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
        ${badge(c.final.status, statusColor)}
        <span style="font-size:13px;color:#6b7280">Rank #${c.final.rank}</span>
        ${c.final.score !== null ? `<span style="font-size:13px;font-weight:700;color:${statusColor}">AI Score: ${c.final.score} / 100</span>` : ''}
      </div>
    </div>
    <div style="text-align:right;font-size:12px;color:#6b7280;flex-shrink:0">
      <div>Generated ${runDate}</div>
      <div style="margin-top:4px">Classical AI Pipeline</div>
      <div>11 stages</div>
    </div>
  </div>

  <!-- Job requirements -->
  ${jobSidebar}

  <!-- Decision -->
  ${section('AI Decision', decisionBody)}

  <!-- Profile -->
  ${section('Resume Profile', profileBody)}

  <!-- Pipeline verdicts -->
  ${section('Pipeline Stage Results', verdictBody)}

  <!-- Eligibility -->
  ${section('Eligibility — BFS / DFS / A*', eligBody)}

  <div class="pagebreak"></div>

  <!-- Heuristic -->
  ${section('Heuristic Score Breakdown', heuristicBody)}

  <!-- CSP -->
  ${section('Constraint Satisfaction (CSP)', cspBody)}

  <!-- Forward chaining -->
  ${section('Forward Chaining', fcBody)}

  <!-- Backward chaining -->
  ${section('Backward Chaining', bcBody)}

  <!-- Resolution -->
  ${section('Resolution Theorem Proving', resBody)}

  <!-- Alpha-Beta -->
  ${section('Alpha-Beta Pruning — Game Tree', abBody)}

  <!-- Footer -->
  <div style="margin-top:32px;padding-top:12px;border-top:1px solid #e5e7eb;font-size:11px;color:#9ca3af;text-align:center">
    Generated by TalentFlow AI · Classical AI Resume Screening System · All decisions are algorithm-based and fully explainable.
  </div>

  <!-- Print button (hidden when printing) -->
  <div class="no-print" style="margin-top:20px;text-align:center">
    <button onclick="window.print()" style="padding:10px 28px;background:#4f46e5;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer">Print / Save as PDF</button>
  </div>

</div>
</body>
</html>`
}

export function downloadReport(c: CandidateResult, job: Job): void {
  const date = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  const html = generateCandidateReport(c, job, date)
  const blob = new Blob([html], { type: 'text/html' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `TalentFlowAI_${c.name.replace(/\s+/g, '_')}_Report.html`
  a.click()
  URL.revokeObjectURL(url)
}

export function downloadAllReports(candidates: CandidateResult[], job: Job): void {
  const date = new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
  // Download one by one with a small delay so browser doesn't block multiple downloads
  candidates.forEach((c, i) => {
    setTimeout(() => {
      const html = generateCandidateReport(c, job, date)
      const blob = new Blob([html], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `TalentFlowAI_${c.name.replace(/\s+/g, '_')}_Report.html`
      a.click()
      URL.revokeObjectURL(url)
    }, i * 400)
  })
}
