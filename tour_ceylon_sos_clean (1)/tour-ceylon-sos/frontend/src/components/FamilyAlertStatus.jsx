import { useState } from 'react'
import { CheckCircle2, MessageCircle, UserPlus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { errorText, touristApi } from '../api'
import { currentPosition } from '../hooks/useLiveTracking'

/** Send the open SOS message and the tourist's current location to a saved family number. */
export default function FamilyAlertStatus({ alerts, onUpdate }) {
  const [sending, setSending] = useState(null)
  const [error, setError] = useState('')
  if (!alerts) return null
  const people = alerts.recipients || []
  if (!people.length) {
    return (
      <section className="card row">
        <UserPlus size={18} color="var(--muted)" />
        <span className="grow">No family number is saved, so nobody was alerted.</span>
        <Link className="btn" to="/safety-card">Add a family number</Link>
      </section>
    )
  }
  const send = async (person) => {
    if (!person.id) return
    setSending(person.id); setError('')
    try {
      const pos = await currentPosition()
      const { data } = await touristApi.post(`/api/family-contacts/${person.id}/send`, pos)
      onUpdate?.(data.family_alerts)
      if (!data.delivered && data.whatsapp_link) window.open(data.whatsapp_link, '_blank', 'noopener')
    } catch (err) {
      const coarse = err?.message === 'coarse' || err?.message === 'no-gps'
      setError(coarse ? 'Turn on precise location, then press Send.' : errorText(err))
    } finally { setSending(null) }
  }
  return (
    <section className="card">
      <h2><MessageCircle size={18} style={{ verticalAlign: '-3px', marginRight: 8 }} />Family alert</h2>
      {people.map((p) => (
        <div className="contact" key={p.phone}>
          <span className="grow"><b>{p.name}</b> <span className="muted">{p.phone}</span></span>
          {p.delivered
            ? <span style={{ color: 'var(--success)', fontWeight: 700 }}><CheckCircle2 size={15} /> Sent</span>
            : <button type="button" className="btn btn-primary" disabled={sending === p.id} onClick={() => send(p)}>{sending === p.id ? 'Sending…' : 'Send'}</button>}
        </div>
      ))}
      <p className="muted" style={{ margin: '8px 0 0' }}>
        Send includes your SOS message and your current location.
      </p>
      {error && <p className="error" role="alert">{error}</p>}
    </section>
  )
}
