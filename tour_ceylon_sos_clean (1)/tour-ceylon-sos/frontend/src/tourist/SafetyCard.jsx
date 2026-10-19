import { useState, useEffect } from 'react'
import { MessageCircle, Trash2 } from 'lucide-react'
import { errorText, touristApi } from '../api'
import { currentPosition } from '../hooks/useLiveTracking'

/** Family / home WhatsApp numbers. They get the SOS automatically. */
export default function SafetyCard() {
  const [contacts, setContacts] = useState([])
  const [max, setMax] = useState(5)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [visa, setVisa] = useState({ visa_type: '', arrival_date: '', visa_expiry: '' })
  const [visaNote, setVisaNote] = useState('')
  const [visaError, setVisaError] = useState('')
  const [visaBusy, setVisaBusy] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [sendingId, setSendingId] = useState(null)
  const [sent, setSent] = useState({})

  useEffect(() => {
    touristApi.get('/api/family-contacts').then(({ data }) => { setContacts(data.contacts); setMax(data.max) }).catch(() => {})
    touristApi.get('/api/auth/tourist/me').then(({ data }) => {
      const t = data.tourist || {}
      setVisa({ visa_type: t.visa_type || '', arrival_date: t.arrival_date || '', visa_expiry: t.visa_expiry || '' })
    }).catch(() => {})
  }, [])

  const add = async (e) => {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const { data } = await touristApi.post('/api/family-contacts', { name, phone })
      setContacts((c) => [...c, data.contact]); setName(''); setPhone('')
    } catch (err) { setError(errorText(err)) } finally { setBusy(false) }
  }
  const send = async (contact) => {
    setSendingId(contact.id); setError('')
    try {
      const pos = await currentPosition()
      const { data } = await touristApi.post(`/api/family-contacts/${contact.id}/send`, pos)
      setSent((s) => ({ ...s, [contact.id]: data.delivered ? 'sent' : 'opened' }))
      if (!data.delivered && data.whatsapp_link) window.open(data.whatsapp_link, '_blank', 'noopener')
    } catch (err) {
      const coarse = err?.message === 'coarse' || err?.message === 'no-gps'
      setError(coarse ? 'Turn on precise location, then press Send.' : errorText(err))
    } finally { setSendingId(null) }
  }
  const saveVisa = async (e) => {
    e.preventDefault(); setVisaBusy(true); setVisaError(''); setVisaNote('')
    try {
      const { data } = await touristApi.patch('/api/auth/tourist/me', visa)
      const t = data.tourist || {}
      setVisa({ visa_type: t.visa_type || '', arrival_date: t.arrival_date || '', visa_expiry: t.visa_expiry || '' })
      const now = new Date()
      const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
      const over = t.visa_expiry && t.visa_expiry < today
      setVisaNote(over ? 'Saved. This visa date is already over.' : 'Saved.')
    } catch (err) { setVisaError(errorText(err)) } finally { setVisaBusy(false) }
  }
  const remove = async (id) => {
    try { await touristApi.delete(`/api/family-contacts/${id}`); setContacts((c) => c.filter((x) => x.id !== id)) }
    catch (err) { setError(errorText(err)) }
  }

  return (
    <>
      <header className="page-head">
        <h1>Safety card</h1>
        <p>Add a family number, then press Send. Your SOS message and current location go to that number.</p>
      </header>
      <section className="card">
        <h2><MessageCircle size={18} style={{ verticalAlign: '-3px', marginRight: 8 }} />Family contacts</h2>
        <p className="muted" style={{ marginTop: 0 }}>Up to {max} numbers. Include the country code.</p>
        {contacts.length === 0 && <p className="muted">No numbers yet.</p>}
        {contacts.map((c) => (
          <div className="contact" key={c.id}>
            <span className="grow"><b>{c.name}</b> <span className="muted">{c.phone}</span></span>
            {sent[c.id] === 'sent'
              ? <span style={{ color: 'var(--success)', fontWeight: 700 }}>Sent</span>
              : <button type="button" className="btn btn-primary" disabled={sendingId === c.id} onClick={() => send(c)}>{sendingId === c.id ? 'Sending…' : 'Send'}</button>}
            <button type="button" className="btn" onClick={() => remove(c.id)} aria-label={`Remove ${c.name}`}><Trash2 size={15} /> Remove</button>
          </div>
        ))}
        {contacts.length < max && (
          <form onSubmit={add} style={{ display: 'grid', gap: 10, marginTop: 14 }}>
            <label className="label">Name<input className="field" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Family contact" /></label>
            <label className="label">WhatsApp number with country code
              <input className="field" required value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+44 7700 900123" inputMode="tel" />
            </label>
            {error && <p className="error" role="alert">{error}</p>}
            <button className="btn btn-primary" disabled={busy}>{busy ? 'Saving…' : 'Add number'}</button>
          </form>
        )}
      </section>
      <section className="card">
        <h2>Visa</h2>
        <p className="muted" style={{ marginTop: 0 }}>The police immigration desk uses this date. A date before today shows as visa over.</p>
        <form onSubmit={saveVisa} style={{ display: 'grid', gap: 10 }}>
          <label className="label">Visa type
            <input className="field" value={visa.visa_type} onChange={(e) => setVisa((v) => ({ ...v, visa_type: e.target.value }))} placeholder="Tourist visa" />
          </label>
          <label className="label">Arrival
            <input className="field" type="date" value={visa.arrival_date} onChange={(e) => setVisa((v) => ({ ...v, arrival_date: e.target.value }))} />
          </label>
          <label className="label">Visa ends
            <input className="field" type="date" required value={visa.visa_expiry} onChange={(e) => setVisa((v) => ({ ...v, visa_expiry: e.target.value }))} />
          </label>
          {visaNote && <p className="muted" style={{ margin: 0 }}>{visaNote}</p>}
          {visaError && <p className="error" role="alert">{visaError}</p>}
          <button className="btn btn-primary" disabled={visaBusy}>{visaBusy ? 'Saving…' : 'Save visa'}</button>
        </form>
      </section>
    </>
  )
}
