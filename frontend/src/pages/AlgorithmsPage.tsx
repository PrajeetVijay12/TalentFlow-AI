import { useEffect, useState } from 'react'
import { api } from '../api'
import { Card, PageHead, PipelineFlow } from '../components/ui'
import type { AlgoInfo } from '../types'

export default function AlgorithmsPage() {
  const [info, setInfo] = useState<AlgoInfo | null>(null)
  useEffect(() => { api.algorithms().then(setInfo).catch(() => setInfo(null)) }, [])

  return (
    <>
      <PageHead title="Algorithm Guide" desc="Where each classical-AI technique is used in this project, in plain language." />
      <Card title="Pipeline"><PipelineFlow /></Card>
      <div style={{ height: 16 }} />
      <Card title="Which algorithm does what" sub="Each one has a real implementation in backend/algorithms/ and its own unit tests.">
        {info ? (
          <div className="table-wrap"><table>
            <thead><tr><th>Algorithm</th><th>Purpose</th><th>Input</th><th>Output</th><th>Source file</th></tr></thead>
            <tbody>{info.table.map(r => (
              <tr key={r.algorithm}><td><b>{r.algorithm}</b></td><td>{r.purpose}</td><td>{r.input}</td><td>{r.output}</td><td className="mono">{r.file}</td></tr>))}</tbody>
          </table></div>
        ) : <span className="muted">Loading…</span>}
      </Card>
      <div style={{ height: 16 }} />
      <Card title="Scoring formula">
        <p className="mono" style={{ margin: 0 }}>h(n) = 0.4·Skills + 0.3·Experience + 0.2·Projects + 0.1·Certifications</p>
        <ul className="small" style={{ paddingLeft: 18 }}>
          <li>Skill score = matched skills ÷ required skills × 100</li>
          <li>Experience score = candidate years ÷ required years × 100 (never above 100)</li>
          <li>Project score: Major = 100, College Major = 80, Mini = 60 (best project counts)</li>
          <li>Certification score = matched certifications ÷ required certifications × 100</li>
          <li>Example: 0.4·80 + 0.3·80 + 0.2·80 + 0.1·25 = <b>74.5</b></li>
        </ul>
      </Card>
      <div className="grid g2" style={{ marginTop: 16 }}>
        {info?.explanations.map(e => (
          <Card key={e.title} title={e.title}><p style={{ margin: 0 }}>{e.body}</p></Card>
        ))}
      </div>
    </>
  )
}
