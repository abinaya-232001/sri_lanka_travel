import { CheckCircle2, Lightbulb, MapPin, Phone, ShieldCheck } from 'lucide-react'

const KIND = { tourism_police: 'Tourism police', nearest_hospital: 'Nearest hospital' }
const tel = (n) => `tel:${String(n || '').replace(/[^\d+]/g, '')}`

/** Detected incident + highlighted tip + nearest police and incident-specific numbers. */
export default function GuidanceCard({ guidance, status }) {
  if (!guidance) return null
  const ml = guidance.classification
  const police = guidance.nearest_police
  const others = (guidance.nearby_contacts || []).filter((c) => c.kind !== 'nearest_police')

  return (
    <section className="card" aria-live="polite">
      <p className="eyebrow">Detected incident</p>
      <div className="row" style={{ marginTop: 4 }}>
        <h2 style={{ margin: 0 }}>{guidance.label}</h2>
        {ml?.confidence != null && <span className="pill">{Math.round(ml.confidence * 100)}% match</span>}
        {status && status !== 'open' && <span className="pill ok">{status === 'acknowledged' ? 'Police have seen it' : status === 'responding' ? 'Police on the way' : status}</span>}
      </div>
      {(!ml || ml.needs_review) && (
        <p className="muted" style={{ margin: '8px 0 0' }}>
          Add more detail in the message field or chat so the station can confirm what happened.
        </p>
      )}

      <div className="tip" role="note">
        <Lightbulb size={20} color="#6E4524" style={{ flexShrink: 0, marginTop: 2 }} aria-hidden="true" />
        <div>
          <p className="eyebrow">Do this now</p>
          <p><strong>{guidance.tip}</strong></p>
        </div>
      </div>
      {guidance.steps?.length > 0 && (
        <ul style={{ margin: '0 0 6px', paddingLeft: 20 }}>{guidance.steps.map((s) => <li key={s}>{s}</li>)}</ul>
      )}

      {police && (
        <div className="contact" style={{ background: '#FBF9F6', borderRadius: 4, padding: 12, border: '1px solid #E7E1D8', borderLeft: '3px solid #2A211C' }}>
          <div className="grow">
            <p className="eyebrow" style={{ color: 'var(--teal)' }}><ShieldCheck size={13} /> Nearest police station</p>
            <b>{police.name}</b>
            {police.distance_km != null && (
              <div className="muted" style={{ fontSize: 13 }}><MapPin size={12} /> {police.distance_km} km away · your location is shared</div>
            )}
          </div>
          <a className="btn btn-danger" href={tel(police.number)}><Phone size={16} /> {police.number}</a>
        </div>
      )}
      {others.map((c) => (
        <div className="contact" key={`${c.kind}-${c.name}`}>
          <div className="grow">
            <p className="eyebrow">{KIND[c.kind] || c.kind}</p>
            <b>{c.name}</b>{c.distance_km != null && <span className="muted"> · {c.distance_km} km</span>}
          </div>
          {c.number && <a className="btn" href={tel(c.number)}><Phone size={14} /> {c.number}</a>}
        </div>
      ))}

      <p className="eyebrow section-label">Numbers for this incident</p>
      <div className="hotlines">
        {guidance.hotlines?.map((h) => (
          <a className="hotline" key={h.kind} href={tel(h.number)}><b>{h.number}</b><span>{h.label}</span></a>
        ))}
      </div>

      {guidance.alert_sent_to?.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <p className="eyebrow">Your alert was sent to</p>
          {guidance.alert_sent_to.map((d) => (
            <div key={d} style={{ color: 'var(--success)', fontSize: 14 }}><CheckCircle2 size={14} /> {d}</div>
          ))}
        </div>
      )}
    </section>
  )
}
