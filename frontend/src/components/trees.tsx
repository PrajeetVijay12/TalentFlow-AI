import type { CriteriaNode, GameTreeNode, ProofNode, TraversalReport } from '../types'
import { Badge } from './ui'

/** BFS / DFS: the criteria tree with PASS / FAIL / SKIPPED on every node. */
function CriteriaItem({ node }: { node: CriteriaNode }) {
  return (
    <li>
      <span className={`tnode ${node.status.toLowerCase()}`}>
        <b>{node.label}</b><Badge status={node.status} />
        {node.leaf && node.required !== null && <span className="small muted">required {node.required} · candidate {node.actual}</span>}
      </span>
      {node.children.length > 0 && <ul>{node.children.map(c => <CriteriaItem key={c.id} node={c} />)}</ul>}
    </li>
  )
}
export const CriteriaTree = ({ node }: { node: CriteriaNode }) => <ul className="tree"><CriteriaItem node={node} /></ul>

export function TraversalTable({ report }: { report: TraversalReport }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>#</th><th>Node visited</th><th>Required</th><th>Candidate</th><th>Result</th></tr></thead>
        <tbody>
          {report.order.map(s => (
            <tr key={s.step}>
              <td className="mono">{s.step}</td>
              <td style={{ paddingLeft: 12 + s.depth * 18 }}>{s.leaf ? s.label : <b>{s.label}</b>} {!s.leaf && <span className="muted small">(group)</span>}</td>
              <td>{s.required ?? '—'}</td><td>{s.actual ?? '—'}</td><td><Badge status={s.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="small muted" style={{ marginTop: 8 }}>
        Visited {report.nodes_visited} of {report.total_nodes} nodes.
        {report.early_stopped && <b style={{ color: 'var(--fail)' }}> Stopped early at “{report.order.find(o => o.id === report.stopped_at)?.label}” — a mandatory criterion failed.</b>}
      </div>
    </div>
  )
}

/** Backward chaining proof tree. */
function ProofItem({ node }: { node: ProofNode }) {
  return (
    <li>
      <span className={`tnode ${node.status.toLowerCase()}`}>
        <b>{node.label}</b><Badge status={node.status} />
        <span className="small muted">{node.via ? `via ${node.via}` : ''} {node.reason && `— ${node.reason}`}</span>
      </span>
      {node.children.length > 0 && <ul>{node.children.map((c, i) => <ProofItem key={i} node={c} />)}</ul>}
    </li>
  )
}
export const ProofTree = ({ node }: { node: ProofNode }) => <ul className="tree"><ProofItem node={node} /></ul>

/** Alpha-Beta game tree with α, β and pruned branches. */
function GameItem({ node, winner }: { node: GameTreeNode; winner?: string | null }) {
  const pruned = !node.visited
  const kind = node.kind.toLowerCase()
  const val = node.kind === 'LEAF' ? node.leaf_value : node.value
  return (
    <li>
      <span className={`tnode ${pruned ? 'pruned' : kind} ${winner === node.id ? 'winner' : ''}`}>
        <span className={`badge nodot ${node.kind === 'MAX' ? 'b-info' : node.kind === 'MIN' ? 'b-wait' : 'b-neutral'}`}>{node.kind}</span>
        <b>{node.label}</b>
        <span className="mono">{pruned ? `(${val})` : `= ${val}`}</span>
        {node.visited && <span className="ab">α=<b>{node.alpha_in_text}</b> β=<b>{node.beta_in_text}</b></span>}
        {pruned && <span className="cut">✂ pruned</span>}
        {node.cutoff && <span className="cut">✂ cut-off: {node.cutoff_reason}</span>}
        {winner === node.id && <span className="badge b-pass">WINNER</span>}
      </span>
      {node.children.length > 0 && <ul>{node.children.map(c => <GameItem key={c.id} node={c} winner={winner} />)}</ul>}
    </li>
  )
}
export const GameTree = ({ node, winner }: { node: GameTreeNode; winner?: string | null }) => <ul className="tree"><GameItem node={node} winner={winner} /></ul>
