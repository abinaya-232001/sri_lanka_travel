import { useCallback, useEffect, useState } from 'react'
import { policeApi } from '../api'
import PoliceShell from './PoliceShell'

const LABELS = { expiring: 'Expiring soon', over: 'Visa over', valid: 'Valid', departed: 'Left the country', unknown: 'Not on file' }

function formatDate(value) {
  if (!value) return '—'
  const [y, m, d] = value.split('-')
  if (!y || !m || !d) return value
  return new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' })
}

function daysLine(row) {
  if (row.status === 'over') return `${Math.abs(row.days)} day${Math.abs(row.days) === 1 ? '' : 's'} over`
  if (row.status === 'expiring') return `${row.days} day${row.days === 1 ? '' : 's'} left`
  if (row.status === 'valid') return `${row.days} days left`
  if (row.status === 'departed') return 'Already left'
  return 'No visa date from the API'
}

export default function ImmigrationPage() {
  const [me, setMe] = useState(null)
  const [records, setRecords] = useState([])
  const [summary, setSummary] = useState(null)
  const [filter, setFilter] = useState('expiring')
  const [error, setError] = useState('')

  const loadMe = useCallback(() => policeApi.get('/api/police/me').then(({ data }) => setMe(data)).catch(() => {}), [])
  const load = useCallback(() => {
    policeApi.get('/api/police/immigration').then(({ data }) => {
      setRecords(data.records || [])
      setSummary(data.summary || null)
      setError('')
    }).catch(() => setError('The immigration desk could not be loaded.'))
  }, [])

  useEffect(() => { loadMe() }, [loadMe])
  useEffect(() => { load() }, [load])

  const shown = filter === 'all' ? records : records.filter((row) => row.status === filter)

  return (
    <PoliceShell station={me?.station} mustChange={me?.must_change_password} onPasswordChanged={loadMe}>
      <header className="page-head">
        <h1>Immigration desk</h1>
        <p>Visa list from the immigration API. Expiring soon means the visa ends within 14 days.</p>
      </header>

      {summary && (
        <div className="visa-stats">
          {[
            ['expiring', summary.expiring],
            ['over', summary.over],
            ['valid', summary.valid],
            ['departed', summary.departed],
            ['all', records.length],
          ].map(([key, count]) => (
            <button key={key} type="button" className={`visa-stat${filter === key ? ' on' : ''}${key === 'over' ? ' danger' : ''}`} onClick={() => setFilter(key)}>
              <strong>{count}</strong>
              <span>{key === 'all' ? 'All records' : LABELS[key]}</span>
            </button>
          ))}
        </div>
      )}

      {error && <p className="error">{error}</p>}

      {shown.length === 0 && <div className="card muted">{filter === 'expiring' ? 'No visa is expiring in the next 14 days.' : 'No records in this group.'}</div>}

      {shown.map((row) => (
        <article key={row.id} className={`card visa-card${row.status === 'over' ? ' is-over' : ''}${row.status === 'expiring' ? ' is-expiring' : ''}`}>
          <div className="row">
            <b className="grow">{row.name}</b>
            <span className={`pill ${row.status === 'over' ? 'open' : row.status === 'valid' ? 'ok' : row.status === 'expiring' ? 'review' : ''}`}>{LABELS[row.status]}</span>
          </div>
          <p className="muted" style={{ margin: '6px 0 0' }}>
            {row.nationality || 'Nationality not given'} · passport {row.passport || 'not given'}
          </p>
          <div className="visa-grid">
            <div><span>Visa</span><strong>{row.visa_type || '—'}</strong></div>
            <div><span>Arrival</span><strong>{formatDate(row.arrival_date)}</strong></div>
            <div><span>Visa ends</span><strong>{formatDate(row.visa_expiry)}</strong></div>
            <div><span>Status</span><strong>{daysLine(row)}</strong></div>
          </div>
        </article>
      ))}
    </PoliceShell>
  )
}
