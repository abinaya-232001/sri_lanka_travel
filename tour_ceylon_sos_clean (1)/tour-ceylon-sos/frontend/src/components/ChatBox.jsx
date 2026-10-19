import { useCallback, useEffect, useRef, useState } from 'react'
import { ImagePlus, Mic, Send, Square } from 'lucide-react'
import { errorText, mediaUrl, policeApi, touristApi } from '../api'
import useIncidentSocket from '../hooks/useIncidentSocket'
import useVoiceRecorder from '../hooks/useVoiceRecorder'

const time = (iso) => (iso ? new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '')

/**
 * Tourist <-> assigned police station chat: text, photos and voice notes, live over Socket.IO.
 * Tourist messages show an English translation for the police; police replies are
 * translated into the tourist's language.
 */
export default function ChatBox({ role, incidentId, title, subtitle, language = 'en', closed = false, onLocation, onIncident }) {
  const api = role === 'police' ? policeApi : touristApi
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const lastId = useRef(0)
  const list = useRef(null)
  const fileInput = useRef(null)
  const voice = useVoiceRecorder(language)

  const load = useCallback(async () => {
    try {
      const { data } = await api.get(`/api/incidents/${incidentId}/messages`, { params: { since_id: lastId.current || undefined } })
      if (data.messages.length) {
        setMessages((prev) => {
          const seen = new Set(prev.map((m) => m.id))
          return [...prev, ...data.messages.filter((m) => !seen.has(m.id))]
        })
        lastId.current = Math.max(lastId.current, ...data.messages.map((m) => m.id))
      }
    } catch { /* next poll retries */ }
  }, [api, incidentId])

  const live = useIncidentSocket(role, incidentId, { onMessage: load, onLocation, onIncident })

  useEffect(() => { lastId.current = 0; setMessages([]); load() }, [load])
  useEffect(() => {
    const t = setInterval(load, live.connected ? 20000 : 4000)
    return () => clearInterval(t)
  }, [load, live.connected])
  useEffect(() => { if (list.current) list.current.scrollTop = list.current.scrollHeight }, [messages, live.otherTyping])

  const send = async (form) => {
    setBusy(true); setError('')
    try {
      const { data } = await api.post(`/api/incidents/${incidentId}/messages`, form)
      setMessages((prev) => (prev.some((m) => m.id === data.message.id) ? prev : [...prev, data.message]))
      lastId.current = Math.max(lastId.current, data.message.id)
      if (data.incident) onIncident?.(data.incident)
      return true
    } catch (err) {
      setError(errorText(err, 'Message not sent. Try again.'))
      return false
    } finally { setBusy(false) }
  }

  const sendText = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    const f = new FormData(); f.append('kind', 'text'); f.append('body', text.trim())
    if (await send(f)) { setText(''); live.stopTyping() }
  }
  const sendImage = async (file) => {
    if (!file) return
    const f = new FormData(); f.append('kind', 'image'); f.append('file', file)
    await send(f)
  }
  const sendVoice = async () => {
    const f = new FormData(); f.append('kind', 'voice'); f.append('file', voice.blob, `voice.${voice.extension}`)
    if (voice.transcript) f.append('voice_transcript', voice.transcript)
    f.append('language', language)
    if (await send(f)) voice.reset()
  }

  const other = role === 'police' ? 'Tourist' : 'Police officer'
  return (
    <section className="card chat">
      <div className="chat-head">
        <p style={{ fontWeight: 700 }}>{title}</p>
        <p style={{ fontSize: 12.5, opacity: 0.9 }}>
          <span className="dot" style={{ background: live.connected ? '#4ade80' : '#cbd5e1', marginRight: 6 }} />
          {live.otherTyping ? `${other} is typing…` : live.connected ? `Live · ${subtitle || ''}` : 'Connecting…'}
        </p>
      </div>
      <div className="chat-body" ref={list}>
        {messages.map((m) => <Bubble key={m.id} m={m} role={role} />)}
        {live.otherTyping && <span className="typing">{other} is typing…</span>}
      </div>
      {error && <p className="error" style={{ margin: '4px 10px' }}>{error}</p>}
      {closed ? (
        <p className="muted" style={{ margin: 0, padding: 12, textAlign: 'center' }}>This case is closed.</p>
      ) : voice.blob && !voice.recording ? (
        <div className="chat-input">
          <span className="grow" style={{ alignSelf: 'center', fontSize: 14 }}>Voice note ready{voice.transcript ? `: “${voice.transcript}”` : ''}</span>
          <button type="button" className="btn" onClick={voice.reset}>Delete</button>
          <button type="button" className="btn btn-primary" disabled={busy} onClick={sendVoice}><Send size={15} /> Send</button>
        </div>
      ) : (
        <form className="chat-input" onSubmit={sendText}>
          <input ref={fileInput} type="file" accept="image/*" hidden onChange={(e) => { sendImage(e.target.files?.[0]); e.target.value = '' }} />
          <button type="button" className="icon-btn" aria-label="Send a photo" disabled={busy || voice.recording} onClick={() => fileInput.current?.click()}><ImagePlus size={18} /></button>
          <input type="text" className="field" value={voice.recording ? '' : text} disabled={voice.recording}
            placeholder={voice.recording ? `Recording… ${voice.seconds}s` : 'Type a message'}
            onChange={(e) => { setText(e.target.value); live.notifyTyping() }} aria-label="Message" />
          <button type="button" className={`icon-btn${voice.recording ? ' mic on' : ''}`} aria-label={voice.recording ? 'Stop recording' : 'Record voice note'}
            onClick={voice.recording ? voice.stop : voice.start} disabled={busy}>
            {voice.recording ? <Square size={15} fill="currentColor" /> : <Mic size={18} />}
          </button>
          <button type="submit" className="icon-btn" aria-label="Send" disabled={busy || voice.recording || !text.trim()}><Send size={17} /></button>
        </form>
      )}
      {voice.error && <p className="error" style={{ margin: '0 10px 8px' }}>{voice.error}</p>}
    </section>
  )
}

function Bubble({ m, role }) {
  if (m.sender_role === 'system') return <div className="bubble system">{String(m.body || '').replace(/^\p{Extended_Pictographic}\uFE0F?\s*/u, '')}</div>
  const mine = m.sender_role === role
  // Police read English; the tourist reads their own language.
  const main = role === 'police' && m.sender_role === 'tourist' ? (m.body_english || m.body) : m.body
  const second = role === 'police' && m.sender_role === 'tourist' && m.body_english && m.body && m.body !== m.body_english
    ? `Original: ${m.body}`
    : role === 'tourist' && m.sender_role === 'police' && m.body_english && m.body !== m.body_english ? `English: ${m.body_english}` : null
  return (
    <div className={`bubble${mine ? ' mine' : ''}`}>
      {m.kind === 'image' && m.media_url && (
        <a href={mediaUrl(m.media_url, role)} target="_blank" rel="noopener noreferrer"><img src={mediaUrl(m.media_url, role)} alt="Photo sent in chat" /></a>
      )}
      {m.kind === 'voice' && m.media_url && <audio controls preload="none" src={mediaUrl(m.media_url, role)} />}
      {main && <div>{m.kind === 'voice' ? <i>“{main}”</i> : main}</div>}
      {second && <div className="translation">{second}</div>}
      <div className="time">{time(m.created_at)}</div>
    </div>
  )
}
