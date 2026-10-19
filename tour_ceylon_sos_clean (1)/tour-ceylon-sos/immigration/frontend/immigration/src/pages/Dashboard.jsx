import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, BadgeCheck, CloudDownload, LogOut, Plane, RefreshCw, Send } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { T, btnPrimary, cardStyle } from '../theme'

function fmtDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' })
}

function SourceBadge({ verified }) {
  return (
    <span
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, fontWeight: 700,
        padding: '3px 8px', borderRadius: 999,
        background: verified ? T.successSoft : T.lineSoft,
        color: verified ? T.success : T.muted,
      }}
    >
      {verified && <BadgeCheck size={13} />}
      {verified ? 'Immigration API' : 'Self-declared'}
    </span>
  )
}

function IntegrationRecord({ row }) {
  return (
    <article style={{ ...cardStyle, padding: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <strong style={{ color: T.navy, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {row.secure_tourist_id} · {row.name} <SourceBadge verified={row.immigration_verified} />
        </strong>
        <span style={{ fontSize: 12, fontWeight: 700, color: row.is_overstay_suspected ? T.danger : T.success }}>
          {row.is_overstay_suspected ? 'Overstay suspected' : row.status_label}
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10, marginTop: 12, fontSize: 13, color: T.muted }}>
        <div><strong>Nationality:</strong> {row.nationality}</div>
        <div><strong>Passport:</strong> {row.passport_verification_status}</div>
        <div><strong>Visa:</strong> {row.visa_type || '—'}</div>
        <div><strong>Validity:</strong> {row.visa_validity_period || '—'}</div>
        <div><strong>Arrival:</strong> {fmtDate(row.arrival_date)}</div>
        <div><strong>Expected departure:</strong> {fmtDate(row.expected_departure_date)}</div>
        <div><strong>Purpose:</strong> {row.travel_purpose || '—'}</div>
        <div><strong>Emergency contact:</strong> {row.emergency_contact?.name || 'Not on file'}</div>
        {row.immigration_reference && <div><strong>Visa reference:</strong> {row.immigration_reference}</div>}
        {row.official_exit_date && <div><strong>Official exit:</strong> {fmtDate(row.official_exit_date)}</div>}
        {row.immigration_sync_error && <div style={{ color: T.danger }}><strong>API:</strong> {row.immigration_sync_error}</div>}
      </div>
    </article>
  )
}

function VisaCard({ card }) {
  return (
    <article style={{ ...cardStyle, padding: 16, borderLeft: card.is_overstay_suspected ? `4px solid ${T.danger}` : `4px solid ${T.navy}` }}>
      <p style={{ margin: 0, fontSize: 11, fontWeight: 800, color: T.muted, letterSpacing: '0.06em' }}>Visa status monitoring</p>
      <p style={{ margin: '8px 0 0', fontWeight: 800, color: T.navy, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        Tourist ID: {card.secure_tourist_id} <SourceBadge verified={card.immigration_verified} />
      </p>
      <div style={{ marginTop: 10, display: 'grid', gap: 6, fontSize: 14 }}>
        <div>Visa Status: <strong>{card.visa_status}</strong></div>
        <div>Arrival: {fmtDate(card.arrival_date)}</div>
        <div>Visa Expiry: {fmtDate(card.visa_expiry)}</div>
        <div>Days Remaining: {card.days_remaining ?? '—'}</div>
        <div>Last Authorized Location Event: {card.last_authorized_location_event || '—'}</div>
        <div>Status: <strong>{card.status_label}</strong></div>
      </div>
    </article>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const officer = JSON.parse(localStorage.getItem('immigrationOfficer') || '{}')
  const [tab, setTab] = useState('visa')
  const [integration, setIntegration] = useState(null)
  const [visaCards, setVisaCards] = useState([])
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const [publishing, setPublishing] = useState(false)
  const [syncing, setSyncing] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [integrationRes, visaRes] = await Promise.all([
        api.get('/api/immigration/integration'),
        api.get('/api/immigration/visa-monitoring'),
      ])
      setIntegration(integrationRes.data)
      setVisaCards(visaRes.data.cards || [])
    } catch (err) {
      setMessage(err.response?.data?.error || 'Failed to load immigration data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const publishAlerts = async () => {
    setPublishing(true)
    setMessage('')
    try {
      const { data } = await api.post('/api/immigration/sync-alerts')
      setMessage(`Published ${data.open_alerts} alert(s) to the police immigration dashboard.`)
    } catch (err) {
      setMessage(err.response?.data?.error || 'Failed to publish alerts')
    } finally {
      setPublishing(false)
    }
  }

  const syncFromApi = async () => {
    setSyncing(true)
    setMessage('')
    try {
      const { data } = await api.post('/api/immigration/sync-from-api')
      setMessage(
        `Immigration API sync: ${data.verified} verified, ${data.not_found} not found, ` +
        `${data.no_passport} without passport, ${data.error} failed.`,
      )
      await load()
    } catch (err) {
      setMessage(err.response?.data?.error || 'Immigration API sync failed')
    } finally {
      setSyncing(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('immigrationToken')
    localStorage.removeItem('immigrationOfficer')
    navigate('/login', { replace: true })
  }

  const overstays = integration?.overstay_suspected || []

  return (
    <div style={{ maxWidth: 1180, margin: '0 auto', padding: '24px 20px 48px' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
        <div>
          <p style={{ margin: 0, fontSize: 12, fontWeight: 800, color: T.muted }}>IMMIGRATION INTEGRATION</p>
          <h1 style={{ margin: '4px 0', color: T.navy, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Plane size={26} /> {officer.department || 'Immigration Dashboard'}
          </h1>
          <p style={{ color: T.muted, maxWidth: 720 }}>{integration?.integration?.data_policy_note}</p>
          {integration?.integration && (
            <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: integration.integration.api_enabled ? T.success : T.danger }}>
              {integration.integration.api_enabled
                ? `Connected: ${integration.integration.provider} · ${integration.summary?.api_verified ?? 0} verified, ${integration.summary?.self_declared ?? 0} self-declared`
                : 'Immigration API not connected. Showing self-declared tourist data.'}
            </p>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button type="button" onClick={load} style={{ ...btnPrimary, background: T.white, color: T.navy, border: `1px solid ${T.line}` }}>
            <RefreshCw size={16} /> Refresh
          </button>
          <button
            type="button"
            onClick={syncFromApi}
            disabled={syncing || !integration?.integration?.api_enabled}
            title={integration?.integration?.api_enabled ? '' : 'Set IMMIGRATION_API_URL on the backend'}
            style={{ ...btnPrimary, background: T.white, color: T.navy, border: `1px solid ${T.line}` }}
          >
            <CloudDownload size={16} /> {syncing ? 'Syncing…' : 'Sync from Immigration API'}
          </button>
          <button type="button" onClick={publishAlerts} disabled={publishing} style={btnPrimary}>
            <Send size={16} /> {publishing ? 'Publishing…' : 'Publish alerts to police'}
          </button>
          <button type="button" onClick={logout} style={{ ...btnPrimary, background: T.lineSoft, color: T.navy }}>
            <LogOut size={16} /> Sign out
          </button>
        </div>
      </header>

      {integration?.legal_notice && (
        <section style={{ ...cardStyle, padding: 14, marginBottom: 14, fontSize: 13, color: T.muted }}>
          {integration.legal_notice}
        </section>
      )}

      {message && <p style={{ ...cardStyle, padding: 12, marginBottom: 12, color: T.navy }}>{message}</p>}

      <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        {['integration', 'visa', 'overstay'].map((key) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            style={{
              ...btnPrimary,
              background: tab === key ? T.navy : T.white,
              color: tab === key ? T.white : T.navy,
              border: `1px solid ${T.line}`,
            }}
          >
            {key === 'integration' ? 'Tourist records' : key === 'visa' ? 'Visa status monitoring' : 'Overstay cases'}
          </button>
        ))}
      </div>

      {loading && <p style={{ color: T.muted }}>Loading…</p>}

      {!loading && tab === 'integration' && (
        <div style={{ display: 'grid', gap: 12 }}>
          {(integration?.records || []).map((row) => <IntegrationRecord key={row.secure_tourist_id} row={row} />)}
        </div>
      )}

      {!loading && tab === 'visa' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12 }}>
          {visaCards.length === 0 && <p style={{ color: T.muted }}>No visa records to monitor.</p>}
          {visaCards.map((card) => <VisaCard key={card.secure_tourist_id} card={card} />)}
        </div>
      )}

      {!loading && tab === 'overstay' && (
        <div style={{ display: 'grid', gap: 12 }}>
          {overstays.length === 0 && <p style={{ color: T.muted }}>No suspected overstay cases.</p>}
          {overstays.map((row) => (
            <article key={row.secure_tourist_id} style={{ ...cardStyle, padding: 16, borderLeft: `4px solid ${T.danger}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: T.danger, fontWeight: 800 }}>
                <AlertTriangle size={18} /> Possible overstay — {row.secure_tourist_id}
              </div>
              <p style={{ margin: '8px 0 0', color: T.muted, fontSize: 13 }}>
                Visa expired {fmtDate(row.visa_valid_to)}. Expected departure {fmtDate(row.expected_departure_date)}.
                Last authorized location: {row.last_authorized_location_event || '—'}.
              </p>
              <p style={{ margin: '8px 0 0', fontSize: 12, color: T.muted }}>{row.location_monitoring_legal_basis}</p>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
