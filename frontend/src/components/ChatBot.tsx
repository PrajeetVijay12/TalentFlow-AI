import { AnimatePresence, motion } from 'framer-motion'
import { type KeyboardEvent, useEffect, useRef, useState } from 'react'
import { api } from '../api'

interface Msg {
  id: number
  role: 'user' | 'bot'
  text: string
}

const SUGGESTIONS = [
  'Summary',
  'Who is rank #1?',
  'Show selected candidates',
  'Why was [name] rejected?',
  'Who knows Python?',
  'Job requirements',
]

// Render **bold** and newlines from bot replies
function BotText({ text }: { text: string }) {
  return (
    <div className="cb-bot-text">
      {text.split('\n').map((line, i) => {
        const parts: React.ReactNode[] = []
        const re = /\*\*(.+?)\*\*/g
        let last = 0; let k = 0; let m: RegExpExecArray | null
        while ((m = re.exec(line)) !== null) {
          if (m.index > last) parts.push(<span key={k++}>{line.slice(last, m.index)}</span>)
          parts.push(<strong key={k++}>{m[1]}</strong>)
          last = m.index + m[0].length
        }
        if (last < line.length) parts.push(<span key={k++}>{line.slice(last)}</span>)
        return <div key={i} style={{ marginTop: i > 0 ? 2 : 0 }}>{parts}</div>
      })}
    </div>
  )
}

export default function ChatBot() {
  const [open, setOpen] = useState(false)
  const [msgs, setMsgs] = useState<Msg[]>([
    {
      id: 0, role: 'bot',
      text: "Hi! I'm your **Knowledge-Based HR Agent**.\n\nAsk me anything about the candidates — scores, reasons, comparisons, skill filters, and more.\n\nTry: 'Summary' or 'Who is rank #1?'",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const nextId = useRef(1)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (open) {
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 80)
      setTimeout(() => inputRef.current?.focus(), 120)
    }
  }, [open, msgs.length])

  async function send(text: string) {
    const msg = text.trim()
    if (!msg || loading) return
    setInput('')
    setMsgs(prev => [...prev, { id: nextId.current++, role: 'user', text: msg }])
    setLoading(true)
    try {
      const res = await api.chat(msg)
      setMsgs(prev => [...prev, { id: nextId.current++, role: 'bot', text: res.reply }])
    } catch {
      setMsgs(prev => [...prev, { id: nextId.current++, role: 'bot', text: '⚠️ Could not reach the server. Is the backend running?' }])
    } finally {
      setLoading(false)
    }
  }

  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send(input) }
  }

  return (
    <div className="cb-root">
      {/* Chat window */}
      <AnimatePresence>
        {open && (
          <motion.div
            className="cb-window"
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.96 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}>

            {/* Header */}
            <div className="cb-header">
              <div className="cb-header-left">
                <div className="cb-avatar-bot">🤖</div>
                <div>
                  <div className="cb-header-title">HR AI Agent</div>
                  <div className="cb-header-sub">Knowledge-Based · Unit I &amp; IV</div>
                </div>
              </div>
              <button className="cb-close" onClick={() => setOpen(false)} aria-label="Close chat">✕</button>
            </div>

            {/* Messages */}
            <div className="cb-messages">
              {msgs.map(m => (
                <div key={m.id} className={`cb-row ${m.role}`}>
                  {m.role === 'bot' && <div className="cb-avatar-sm">🤖</div>}
                  <div className={`cb-bubble ${m.role}`}>
                    {m.role === 'bot' ? <BotText text={m.text} /> : m.text}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="cb-row bot">
                  <div className="cb-avatar-sm">🤖</div>
                  <div className="cb-bubble bot cb-thinking">
                    <span /><span /><span />
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Quick suggestions (shown only when few messages) */}
            {msgs.length <= 2 && (
              <div className="cb-suggestions">
                {SUGGESTIONS.map(s => (
                  <button key={s} className="cb-chip" onClick={() => send(s)}>{s}</button>
                ))}
              </div>
            )}

            {/* Input */}
            <div className="cb-input-row">
              <input
                ref={inputRef}
                className="cb-input"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={onKey}
                placeholder="Ask about candidates…"
                disabled={loading}
              />
              <button className="cb-send" onClick={() => send(input)} disabled={loading || !input.trim()} aria-label="Send">
                {loading ? <span className="cb-spin" /> : '➤'}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* FAB trigger button */}
      <motion.button
        className="cb-fab"
        onClick={() => setOpen(o => !o)}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.94 }}
        aria-label="Open HR AI chatbot">
        <AnimatePresence mode="wait">
          {open
            ? <motion.span key="x" initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: 90, opacity: 0 }} transition={{ duration: 0.18 }}>✕</motion.span>
            : <motion.span key="bot" initial={{ rotate: 90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} exit={{ rotate: -90, opacity: 0 }} transition={{ duration: 0.18 }}>🤖</motion.span>
          }
        </AnimatePresence>
        {!open && <span className="cb-fab-label">Ask AI</span>}
      </motion.button>
    </div>
  )
}
