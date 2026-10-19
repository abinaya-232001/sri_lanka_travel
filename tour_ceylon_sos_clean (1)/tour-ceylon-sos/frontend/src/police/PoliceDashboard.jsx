import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { policeApi } from '../api'
import LiveMap from '../components/LiveMap'
import ActivityStatus from '../components/ActivityStatus'
import { connectSocket } from '../socket'
import PoliceShell from './PoliceShell'

const ago = (iso) => { const m = Math.round((Date.now() - new Date(iso)) / 60000); return m < 1 ? 'just now' : m < 60 ? `${m} min ago` : `${Math.round(m / 60)} h ago` }

function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const o = ctx.createOscillator(); o.frequency.value = 880; o.connect(ctx.destination); o.start(); o.stop(ctx.currentTime + 0.4)
  } catch { /* sound optional */ }
}

export default function PoliceDashboard() {
  const navigate = useNavigate()
  const [me, setMe] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [visaWatch, setVisaWatch] = useState({ expiring: [], over: [] })
  const [showAll, setShowAll] = useState(false)
  const [live, setLive] = useState(false)

  const load = useCallback(async () => {
    try { const { data } = await policeApi.get('/api/police/incidents', { params: { active: showAll ? 0 : 1 } }); setIncidents(data.incidents) } catch { /* retry */ }
  }, [showAll])
  const loadMe = useCallback(() => policeApi.get('/api/police/me').then(({ data }) => setMe(data)).catch(() => {}), [])

  useEffect(() => { loadMe() }, [loadMe])
  useEffect(() => {
    policeApi.get('/api/police/immigration').then(({ data }) => {
      const records = data.records || []
      setVisaWatch({
        expiring: records.filter((row) => row.status === 'expiring'),
        over: records.filter((row) => row.status === 'over'),
      })
    }).catch(() => {})
  }, [])
  useEffect(() => { load(); const t = setInterval(load, live ? 30000 : 8000); return () => clearInterval(t) }, [load, live])
  useEffect(() => {
    const s = connectSocket('police')
    if (!s) return undefined
    s.on('connect', () => setLive(true)); s.on('disconnect', () => setLive(false))
    s.on('sos:new', (inc) => { beep(); setIncidents((list) => [inc, ...list.filter((i) => i.id !== inc.id)]) })
    s.on('incident:update', (inc) => setIncidents((list) => list.map((i) => (i.id === inc.id ? inc : i))))
    return () => s.disconnect()
  }, [])

  return (
    <PoliceShell station={me?.station} mustChange={me?.must_change_password} onPasswordChanged={loadMe}>
      {(visaWatch.expiring.length > 0 || visaWatch.over.length > 0) && (
        <Link to="/police/immigration" className="card visa-over-banner">
          <div className="grow">
            <b>{visaWatch.expiring.length > 0 ? 'Visas expiring' : 'Visa over'}</b>
            <p>
              {visaWatch.expiring.length > 0 && `${visaWatch.expiring.length} from the immigration API end within 14 days.`}
              {visaWatch.expiring.length > 0 && visaWatch.over.length > 0 && ' '}
              {visaWatch.over.length > 0 && `${visaWatch.over.length} already over.`}
            </p>
          </div>
          <span className="btn btn-primary">Open immigration desk</span>
        </Link>
      )}
      <header className="page-head row police-band">
        <div className="grow">
          <h1>{showAll ? 'All cases' : 'Open cases'}</h1>
          <p>{incidents.length} {showAll ? (incidents.length === 1 ? 'case on record' : 'cases on record') : (incidents.length === 1 ? 'open case' : 'open cases')}</p>
        </div>
        <span className="muted"><span className="dot" style={{ background: live ? 'var(--success)' : '#B7A99A', marginRight: 6 }} />{live ? 'Live' : 'Reconnecting'}</span>
        <button type="button" className="btn" onClick={() => setShowAll((v) => !v)}>{showAll ? 'Open cases' : 'All cases'}</button>
      </header>
      <div className="grid-2">
        <div>
          {incidents.length === 0 && <div className="card muted">No {showAll ? '' : 'open '}cases for this station.</div>}
          {incidents.map((i) => (
            <Link key={i.id} to={`/police/incidents/${i.id}`} className="card incident-row"
              style={{ borderLeftColor: i.status === 'open' ? 'var(--danger)' : i.is_open === false ? 'var(--line)' : 'var(--warn)' }}>
              <div className="row">
                <b className="grow">#{i.id} · {i.label}</b>
                <span className={`pill ${i.status === 'open' ? 'open' : ''}`}>{i.status}</span>
                {i.classification?.needs_review && <span className="pill review">Needs review</span>}
              </div>
              <span>{i.tourist?.name} <span className="muted">· {i.tourist?.nationality || 'Nationality not given'} · {ago(i.created_at)}</span></span>
              {i.message_english && <span className="muted">“{i.message_english.slice(0, 140)}”</span>}
              <span className={i.tracking_active ? 'track-on' : 'track-off'}>
                Live location {i.tracking_active ? 'on' : 'off'}
              </span>
              <ActivityStatus status={i.status} />
            </Link>
          ))}
        </div>
        {me?.station ? (
          <LiveMap incidents={incidents.filter((i) => i.tracking_active || i.status !== 'closed')} station={me.station}
            onSelect={(i) => navigate(`/police/incidents/${i.id}`)} height={520} />
        ) : <div className="map" style={{ height: 520 }} />}
      </div>
    </PoliceShell>
  )
}
