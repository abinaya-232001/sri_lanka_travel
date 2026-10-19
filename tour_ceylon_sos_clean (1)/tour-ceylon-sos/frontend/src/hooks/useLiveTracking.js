import { useEffect, useRef } from 'react'
import { touristApi } from '../api'

const MIN_INTERVAL_MS = 10000
const MIN_MOVE_M = 15
const MAX_ACCURACY_M = 1000

function meters(a, b) {
  const R = 6371000, rad = (d) => (d * Math.PI) / 180
  const x = Math.sin(rad(b.lat - a.lat) / 2) ** 2 + Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(rad(b.lng - a.lng) / 2) ** 2
  return 2 * R * Math.asin(Math.sqrt(x))
}

/**
 * Sends the tourist's GPS position to the open case until sharing is turned off.
 * Pings every 10 s while moving (and at least every 60 s while still) so police see the route.
 */
export default function useLiveTracking(incidentId, active, { onPing, onStopped } = {}) {
  const last = useRef(null)
  const cb = useRef({ onPing, onStopped })
  cb.current = { onPing, onStopped }

  useEffect(() => {
    if (!incidentId || !active || !navigator.geolocation) return undefined
    last.current = null
    const send = async ({ coords }) => {
      if (coords.accuracy != null && coords.accuracy > MAX_ACCURACY_M) return
      const now = Date.now()
      const pos = { lat: coords.latitude, lng: coords.longitude }
      const prev = last.current
      if (prev && now - prev.t < MIN_INTERVAL_MS) return
      if (prev && meters(prev, pos) < MIN_MOVE_M && now - prev.t < 60000) return
      last.current = { ...pos, t: now }
      try {
        await touristApi.post(`/api/sos/${incidentId}/location`, {
          latitude: coords.latitude, longitude: coords.longitude, accuracy: coords.accuracy,
        })
        cb.current.onPing?.(now)
      } catch (err) {
        if (err?.response?.status === 409) cb.current.onStopped?.()
      }
    }
    const id = navigator.geolocation.watchPosition(send, () => {}, { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 })
    return () => navigator.geolocation.clearWatch(id)
  }, [incidentId, active])
}

export function currentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) { reject(new Error('no-gps')); return }
    navigator.geolocation.getCurrentPosition(
      (p) => {
        if (p.coords.accuracy != null && p.coords.accuracy > MAX_ACCURACY_M) {
          reject(new Error('coarse'))
          return
        }
        resolve({ latitude: p.coords.latitude, longitude: p.coords.longitude, accuracy: p.coords.accuracy })
      },
      reject,
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 30000 },
    )
  })
}
