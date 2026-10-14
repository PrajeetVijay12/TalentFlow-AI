import type { FCResult } from '../types'

/** Forward chaining shown as a vertical inference chain: Facts → Rule fired → Derived fact → ... */
export function ChainView({ fc }: { fc: FCResult }) {
  const relevant = fc.initial_facts.filter(f => !f.startsWith('cgpa(') && !f.startsWith('degree('))
  return (
    <div className="chain">
      <div className="step fact"><b>Known facts</b><div className="small">{relevant.map(f => <span key={f} className="chip">{f}</span>)}</div></div>
      {fc.fired.map(f => (
        <div key={f.rule}>
          <div className="down">↓</div>
          <div className="step rule"><b>{f.rule} fired</b> <span className="small muted">(round {f.round})</span>
            <div className="small">{f.text}</div>
            <div className="small">using <span className="mono">{f.premises.join(' ∧ ')}</span></div>
            <div style={{ marginTop: 4 }}>⇒ <b className="mono">{f.derived} = TRUE</b></div></div>
        </div>
      ))}
      {fc.blocked.length > 0 && <>
        <div className="down">⋮</div>
        {fc.blocked.filter(b => b.derived === 'eligible' || b.derived === 'technical_skill' || b.derived === 'academic_fit' || b.derived === 'technical_fit').map(b => (
          <div key={b.rule} className="step bad" style={{ marginBottom: 4 }}><b>{b.rule} could NOT fire</b>
            <div className="small">{b.text}</div><div className="small">missing: <span className="mono">{b.missing.join(', ')}</span></div></div>
        ))}
      </>}
      <div className="down">↓</div>
      <div className={`step ${fc.goal_reached ? 'result' : 'bad'}`}><b>eligible = {fc.goal_reached ? 'TRUE' : 'NOT DERIVED'}</b>
        <div className="small">{fc.fired.length} rule(s) fired in {fc.rounds} round(s).</div></div>
    </div>
  )
}
