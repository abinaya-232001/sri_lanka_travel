import { useCallback, useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { errorText, touristApi } from '../api'
import LiveLocationBanner from '../components/LiveLocationBanner'
import useLiveTracking, { currentPosition } from '../hooks/useLiveTracking'

/**
 * Holds the tourist's open case for every page, so live location keeps going
 * on any page until the tourist turns it off.
 */
export default function TouristLayout() {
  const navigate = useNavigate()
  const [me, setMe] = useState(null)
  const [incident, setIncident] = useState(null)
  const [sending, setSending] = useState(false)
  const [sosError, setSosError] = useState('')
  const [lastPingAt, setLastPingAt] = useState(null)

  const refresh = useCallback(async () => {
    try {
      const { data } = await touristApi.get('/api/sos/current')
      setIncident((prev) => (data.incident ? { ...data.incident, family_alerts: data.incident.family_alerts || prev?.family_alerts } : null))
    } catch { /* offline: keep last state */ }
  }, [])

  useEffect(() => {
    touristApi.get('/api/auth/tourist/me').then(({ data }) => setMe(data.tourist)).catch(() => {})
    refresh()
    const t = setInterval(refresh, 15000)
    return () => clearInterval(t)
  }, [refresh])

  useLiveTracking(incident?.id, Boolean(incident?.tracking_active), { onPing: setLastPingAt, onStopped: refresh })

  const sendSos = useCallback(async ({ message, voice, transcript, extension }) => {
    setSending(true); setSosError('')
    try {
      let pos
      try { pos = await currentPosition() } catch (err) {
        setSosError(err?.message === 'coarse'
          ? 'This location is only a city guess, not your real position. Turn on precise location, then press SOS again.'
          : 'Turn on location (GPS) for this site — police need it to find you. Then press SOS again.')
        return false
      }
      const form = new FormData()
      form.append('latitude', pos.latitude); form.append('longitude', pos.longitude); form.append('accuracy', pos.accuracy ?? '')
      form.append('language', me?.language || 'en')
      if (message) form.append('message', message)
      if (voice) {
        form.append('voice', voice, `sos.${extension || 'webm'}`)
        if (transcript) form.append('voice_transcript', transcript)
      }
      const { data } = await touristApi.post('/api/sos', form)
      setIncident(data.incident)
      if (navigator.vibrate) navigator.vibrate([80, 40, 80])
      navigate('/')
      return true
    } catch (err) {
      setSosError(errorText(err, 'SOS not sent. Check your connection and try again, or call 119.'))
      return false
    } finally { setSending(false) }
  }, [me, navigate])

  const setSharing = useCallback(async (on) => {
    if (!incident) return
    try {
      const { data } = await touristApi.post(`/api/sos/${incident.id}/tracking`, { active: on })
      setIncident((prev) => ({ ...prev, tracking_active: data.tracking_active }))
    } catch (err) {
      if (err?.response?.status === 409) refresh()
      else alert(errorText(err))
    }
  }, [incident, refresh])

  return (
    <div className="sos-desk">
      <div className="app-sub">
        <div className="app-sub-inner">
          <nav aria-label="SOS">
            <NavLink to="/" end>Dashboard</NavLink>
            <NavLink to="/safety-card">Safety card</NavLink>
          </nav>
        </div>
        {incident && (
          <LiveLocationBanner sharing={incident.tracking_active} stationName={incident.station?.name}
            lastPingAt={lastPingAt} onChange={setSharing} />
        )}
      </div>
      <main className="page">
        <Outlet context={{ me, incident, setIncident, refresh, sendSos, sending, sosError }} />
      </main>
    </div>
  )
}
