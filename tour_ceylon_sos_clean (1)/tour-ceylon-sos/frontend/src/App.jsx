import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { session } from './api'
import DashboardChrome from './components/DashboardChrome'
import TouristLayout from './tourist/TouristLayout'
import TouristDashboard from './tourist/TouristDashboard'
import SafetyCard from './tourist/SafetyCard'
import PoliceLogin from './police/PoliceLogin'
import PoliceDashboard from './police/PoliceDashboard'
import IncidentPage from './police/IncidentPage'
import ImmigrationPage from './police/ImmigrationPage'

const TRAVEL = 'http://127.0.0.1:5000'

function AccountGate({ children }) {
  const [ready, setReady] = useState(() => !new URLSearchParams(window.location.search).get('handoff'))
  useEffect(() => {
    const handoff = new URLSearchParams(window.location.search).get('handoff')
    if (!handoff) return undefined
    let cancelled = false
    fetch('/api/auth/handoff', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: handoff }),
    }).then(async (r) => {
      const data = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(data.error || 'handoff')
      session.set('tourist', data.token)
      const url = new URL(window.location.href)
      url.searchParams.delete('handoff')
      window.history.replaceState({}, '', url.pathname + url.search + url.hash)
      if (!cancelled) setReady(true)
    }).catch(() => {
      session.clear('tourist')
      window.location.replace(`${TRAVEL}/#/sos`)
    })
    return () => { cancelled = true }
  }, [])
  if (!ready) return <p className="muted" style={{ padding: 28 }}>Opening your TourCeylon account…</p>
  return children
}

function Guard({ role, children }) {
  if (!session.get(role)) {
    if (role === 'police') return <Navigate to="/police/login" replace />
    window.location.replace(`${TRAVEL}/#/sos`)
    return null
  }
  return children
}

export default function App() {
  return (
    <AccountGate>
    <Routes>
      <Route path="/login" element={<Navigate to="/" replace />} />
      <Route element={<DashboardChrome><Guard role="tourist"><TouristLayout /></Guard></DashboardChrome>}>
        <Route path="/" element={<TouristDashboard />} />
        <Route path="/safety-card" element={<SafetyCard />} />
      </Route>
      <Route path="/police/login" element={<PoliceLogin />} />
      <Route path="/police" element={<Guard role="police"><PoliceDashboard /></Guard>} />
      <Route path="/police/immigration" element={<Guard role="police"><ImmigrationPage /></Guard>} />
      <Route path="/police/incidents/:id" element={<Guard role="police"><IncidentPage /></Guard>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </AccountGate>
  )
}
