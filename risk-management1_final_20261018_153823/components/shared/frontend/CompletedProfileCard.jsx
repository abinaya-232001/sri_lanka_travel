function mediaSrc(url) {
  if (!url) return null
  if (url.startsWith('http') || url.startsWith('blob:')) return url
  return url.startsWith('/') ? url : `/${url}`
}

function initials(name) {
  const parts = String(name || '')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  if (!parts.length) return 'TC'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
}

function Row({ label, value }) {
  if (!value) return null
  return (
    <div style={{ minWidth: 0 }}>
      <div
        style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: '0.08em',
          textTransform: 'uppercase',
          color: '#7A9A9E',
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 14.5, fontWeight: 650, color: '#0D2C30', wordBreak: 'break-word' }}>{value}</div>
    </div>
  )
}

export default function CompletedProfileCard({ tourist, t, onEdit }) {
  const photo = mediaSrc(tourist.photo_url || tourist.photo_path)
  const ec = tourist.emergency_contact || {}
  const trip =
    tourist.trip_start || tourist.trip_end
      ? [tourist.trip_start, tourist.trip_end].filter(Boolean).join('  →  ')
      : ''

  return (
    <article
      style={{
        width: '100%',
        maxWidth: 560,
        margin: '0 auto',
        borderRadius: 22,
        overflow: 'hidden',
        background: '#fff',
        border: '1px solid rgba(10, 74, 82, 0.12)',
        boxShadow: '0 18px 48px rgba(10, 74, 82, 0.12)',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      <div
        style={{
          background: 'linear-gradient(125deg, #0A4A52 0%, #12707A 55%, #2EB8C4 100%)',
          padding: '18px 20px 16px',
          color: '#fff',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: 12,
        }}
      >
        <div>
          <div style={{ fontSize: 10, fontWeight: 800, letterSpacing: '0.16em', opacity: 0.82 }}>
            TOUR CEYLON
          </div>
          <div style={{ marginTop: 4, fontSize: 18, fontWeight: 800, letterSpacing: '-0.02em' }}>
            {t('visitorPass') || 'Visitor pass'}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <span
            style={{
              background: 'rgba(255,255,255,0.16)',
              border: '1px solid rgba(255,255,255,0.28)',
              borderRadius: 999,
              padding: '6px 12px',
              fontSize: 11,
              fontWeight: 800,
              letterSpacing: '0.04em',
            }}
          >
            {t('profileLocked') || 'Completed'}
          </span>
          {onEdit && (
            <button
              type="button"
              onClick={onEdit}
              style={{
                background: '#fff',
                color: '#0A4A52',
                border: 'none',
                borderRadius: 999,
                padding: '7px 14px',
                fontSize: 12,
                fontWeight: 800,
                letterSpacing: '0.02em',
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              {t('editProfile') || 'Edit'}
            </button>
          )}
        </div>
      </div>

      <div style={{ padding: '20px 20px 8px', display: 'flex', gap: 16, alignItems: 'center' }}>
        <div
          style={{
            width: 92,
            height: 92,
            borderRadius: 18,
            overflow: 'hidden',
            flexShrink: 0,
            background: 'linear-gradient(160deg, #DDF2F3, #B7E4E6)',
            display: 'grid',
            placeItems: 'center',
            color: '#0A4A52',
            fontWeight: 800,
            fontSize: 28,
            boxShadow: '0 8px 20px rgba(10, 74, 82, 0.12)',
          }}
        >
          {photo ? (
            <img src={photo} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            initials(tourist.name)
          )}
        </div>
        <div style={{ minWidth: 0 }}>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800, color: '#0A4A52', lineHeight: 1.15 }}>
            {tourist.name || t('visitor')}
          </h2>
          <p style={{ margin: '6px 0 0', color: '#4A6B70', fontSize: 13.5, fontWeight: 600 }}>
            {tourist.nationality}
            {tourist.email ? ` · ${tourist.email}` : ''}
          </p>
          {tourist.secure_tourist_id && (
            <p
              style={{
                margin: '10px 0 0',
                display: 'inline-block',
                background: '#E8F6F6',
                color: '#0A4A52',
                borderRadius: 8,
                padding: '5px 10px',
                fontSize: 12,
                fontWeight: 800,
                letterSpacing: '0.04em',
                fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
              }}
            >
              {tourist.secure_tourist_id}
            </p>
          )}
        </div>
      </div>

      <div
        style={{
          margin: '8px 20px 0',
          padding: '16px 0 4px',
          borderTop: '1px solid #E2EEF0',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '16px 18px',
        }}
      >
        <Row label={t('phone')} value={tourist.phone} />
        <Row label={t('passportNic')} value={tourist.passport_or_nic} />
        <Row label={t('tripDates') || t('tripStart')} value={trip} />
        <Row label={t('hotelName')} value={tourist.hotel_name} />
        <Row label={t('hotelContact')} value={tourist.hotel_contact} />
      </div>

      <div style={{ margin: '4px 20px 20px', paddingTop: 14, borderTop: '1px solid #E2EEF0' }}>
        <div
          style={{
            fontSize: 10,
            fontWeight: 800,
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
            color: '#7A9A9E',
            marginBottom: 10,
          }}
        >
          {t('emergencyContact')}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px 18px' }}>
          <Row label={t('emergencyName')} value={ec.name} />
          <Row label={t('emergencyPhone')} value={ec.phone} />
          <Row label={t('emergencyRelationship')} value={ec.relationship} />
          <Row label={t('emergencyEmail')} value={ec.email} />
        </div>
      </div>

      <div
        style={{
          padding: '10px 20px 14px',
          background: '#F7FBFC',
          color: '#5A7A7E',
          fontSize: 12,
          fontWeight: 600,
          textAlign: 'center',
        }}
      >
        {onEdit ? t('profileEditHint') || 'Tap Edit to update your visitor pass.' : t('profileLockedHint')}
      </div>
    </article>
  )
}
