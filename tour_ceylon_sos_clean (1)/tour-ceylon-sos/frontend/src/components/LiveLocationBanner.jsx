import { useEffect, useState } from 'react'
import { MapPin, MapPinOff } from 'lucide-react'

/** Shown on every tourist page while a case is open. Only the tourist can stop sharing. */
export default function LiveLocationBanner({ sharing, stationName, lastPingAt, onChange }) {
  const [confirm, setConfirm] = useState(false)
  const [busy, setBusy] = useState(false)
  const [, tick] = useState(0)
  useEffect(() => { const t = setInterval(() => tick((n) => n + 1), 5000); return () => clearInterval(t) }, [])
  const ago = lastPingAt ? Math.round((Date.now() - lastPingAt) / 1000) : null
  const change = async (on) => { setBusy(true); try { await onChange(on); setConfirm(false) } finally { setBusy(false) } }

  return (
    <div className={`live-banner ${sharing ? 'on' : 'off'}`} role="status" aria-live="polite">
      <span className="live-dot" />
      {sharing ? <MapPin size={16} /> : <MapPinOff size={16} />}
      <span className="grow">
        {sharing
          ? <><b>Live location is on</b> for {stationName || 'the station'}{ago != null && <span className="muted"> · updated {ago < 60 ? `${ago}s` : `${Math.round(ago / 60)} min`} ago</span>}</>
          : <><b>Live location is off.</b> The station can only see your last position.</>}
      </span>
      {sharing && !confirm && <button type="button" onClick={() => setConfirm(true)}>Stop sharing</button>}
      {sharing && confirm && (
        <span className="row" style={{ gap: 6 }}>
          <span style={{ fontSize: 13 }}>Police won’t see where you go.</span>
          <button type="button" disabled={busy} onClick={() => change(false)}>Yes, stop</button>
          <button type="button" className="solid" disabled={busy} onClick={() => setConfirm(false)}>Keep sharing</button>
        </span>
      )}
      {!sharing && <button type="button" className="solid" disabled={busy} onClick={() => change(true)}>Turn on again</button>}
    </div>
  )
}
