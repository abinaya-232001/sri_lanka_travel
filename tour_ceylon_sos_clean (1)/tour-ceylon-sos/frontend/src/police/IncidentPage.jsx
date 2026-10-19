import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Phone } from 'lucide-react'
import { errorText, policeApi } from '../api'
import ChatBox from '../components/ChatBox'
import ActivityStatus from '../components/ActivityStatus'
import LiveMap from '../components/LiveMap'
import PoliceShell from './PoliceShell'

const LANG = { en: 'English', si: 'Sinhala', ta: 'Tamil', de: 'German', fr: 'French', es: 'Spanish', it: 'Italian', ru: 'Russian', zh: 'Chinese', ja: 'Japanese', ko: 'Korean', hi: 'Hindi', ar: 'Arabic', nl: 'Dutch', pt: 'Portuguese' }
const languageName = (code) => LANG[code] || code || 'not given'
const LABEL = { animal_attack: 'Animal Attack', physical_assault: 'Physical Assault', sexual_assault: 'Sexual Assault', medical: 'Medical',
  accident: 'Road Accident', fire: 'Fire', theft: 'Theft / Robbery', harassment: 'Harassment / Threat', missing_person: 'Missing Person',
  lost_rescue: 'Lost / Rescue', drowning: 'Drowning', natural_disaster: 'Natural Disaster', lost_passport: 'Lost Passport',
  financial_fraud: 'Financial Fraud', other: 'Other' }
const t = (iso) => (iso ? new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '')

export default function IncidentPage() {
  const { id } = useParams()
  const [inc, setInc] = useState(null)
  const [track, setTrack] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')

  const load = useCallback(async () => {
    try {
      const [a, b] = await Promise.all([policeApi.get(`/api/police/incidents/${id}`), policeApi.get(`/api/incidents/${id}/pings`)])
      setInc(a.data.incident); setTrack(b.data.pings); setError('')
    } catch (err) { setError(errorText(err, 'Could not load this case.')) }
  }, [id])
  useEffect(() => { load(); const timer = setInterval(load, 20000); return () => clearInterval(timer) }, [load])

  const onLocation = useCallback((p) => setTrack((list) => (list.some((x) => x.id === p.id) ? list : [...list, p])), [])
  const onIncident = useCallback((data) => setInc(data), [])

  const setStatus = async (status) => {
    setBusy(status)
    try { const { data } = await policeApi.post(`/api/police/incidents/${id}/status`, { status }); setInc(data.incident) }
    catch (err) { setError(errorText(err)) } finally { setBusy('') }
  }

  if (!inc) return <PoliceShell><p className={error ? 'error' : 'muted'}>{error || 'Loading…'}</p></PoliceShell>
  const ml = inc.classification
  const lastOff = [...(inc.tracking_events || [])].reverse().find((e) => !e.active)
  const tel = (n) => `tel:${String(n || '').replace(/[^\d+]/g, '')}`

  return (
    <PoliceShell station={inc.station}>
      <Link to="/police" className="btn btn-quiet" style={{ marginBottom: 8, paddingLeft: 0 }}><ArrowLeft size={15} /> All cases</Link>
      <header className="page-head row">
        <h1 className="grow">Case {inc.id} · {inc.label}</h1>
        <span className={`pill ${inc.status === 'open' ? 'open' : 'ok'}`}>{inc.status}</span>
      </header>
      <ActivityStatus status={inc.status} />
      {error && <p className="error">{error}</p>}
      <div className="grid-2">
        <div>
          <LiveMap track={track} station={inc.station} />
          <div className="card" style={{ marginTop: 12, background: inc.tracking_active ? 'var(--success-soft)' : 'var(--warn-soft)' }}>
            <b className={inc.tracking_active ? 'track-on' : 'track-off'}>Live location {inc.tracking_active ? 'on' : 'off'}</b>
            <span className="muted" style={{ marginLeft: 8 }}>
              {inc.tracking_active
                ? `Red line is the route since SOS · ${track.length} points · last update ${t(track[track.length - 1]?.recorded_at)}`
                : lastOff?.by === 'tourist' ? `The tourist stopped sharing at ${t(lastOff.at)}. The map shows the last known position.` : 'The map shows the last known position.'}
            </span>
          </div>
          <ChatBox role="police" incidentId={inc.id} title={`Chat with ${inc.tourist?.name || 'tourist'}`}
            subtitle={`speaks ${languageName(inc.tourist?.language)} · messages are translated`} closed={inc.status === 'closed'}
            onLocation={onLocation} onIncident={onIncident} />
        </div>
        <div>
          <section className="card">
            <p className="eyebrow">Tourist</p>
            <b style={{ fontSize: 17 }}>{inc.tourist?.name}</b>
            <div className="muted">{inc.tourist?.nationality || 'Nationality not given'} · passport {inc.tourist?.passport || 'not given'} · speaks {languageName(inc.tourist?.language)}</div>
            {inc.tourist?.phone && <a className="btn btn-primary" style={{ marginTop: 10 }} href={tel(inc.tourist.phone)}><Phone size={15} /> {inc.tourist.phone}</a>}
          </section>
          <section className="card">
            <p className="eyebrow">SOS message</p>
            <p style={{ margin: '6px 0' }}>{inc.message_english ? `“${inc.message_english}”` : <i className="muted">One-tap SOS (no message yet)</i>}</p>
            {inc.message_original && inc.message_original !== inc.message_english && (
              <p className="muted" style={{ margin: 0, fontSize: 13.5 }}>Original ({inc.original_language}): {inc.message_original}</p>
            )}
            <p className="eyebrow section-label">Incident type</p>
            {ml ? (
              <div>
                <b>{LABEL[ml.incident_type] || ml.incident_type}</b> · {Math.round(ml.confidence * 100)}% confidence
                {ml.needs_review && <span className="pill review" style={{ marginLeft: 8 }}>Confirm with the tourist</span>}
                {ml.alternatives?.length > 0 && (
                  <div className="muted">Other possibilities: {ml.alternatives.map((a) => `${LABEL[a.incident_type] || a.incident_type} ${Math.round(a.confidence * 100)}%`).join(', ')}</div>
                )}
              </div>
            ) : <span className="muted">No message to classify.</span>}
            <p className="eyebrow section-label">Tip shown to the tourist</p>
            <p style={{ margin: '4px 0 0' }}>{inc.guidance?.tip}</p>
          </section>
          <section className="card">
            <p className="eyebrow">Status the tourist can see</p>
            <div className="row" style={{ marginTop: 8 }}>
              {[['acknowledged', 'Seen'], ['responding', 'On the way'], ['resolved', 'Resolved'], ['closed', 'Close case']].map(([s, label]) => (
                <button key={s} type="button" className={`btn ${s === 'resolved' ? 'btn-primary' : ''}`} disabled={busy || inc.status === s || inc.status === 'closed'}
                  onClick={() => setStatus(s)}>{busy === s ? '…' : label}</button>
              ))}
            </div>
          </section>
        </div>
      </div>
    </PoliceShell>
  )
}
