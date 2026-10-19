import { useCallback, useEffect, useRef, useState } from 'react'
import { connectSocket } from '../socket'

/**
 * Live events for one incident: chat messages, typing, location and status.
 * Falls back gracefully: callers keep a slow poll while `connected` is false.
 */
export default function useIncidentSocket(role, incidentId, handlers = {}) {
  const [connected, setConnected] = useState(false)
  const [otherTyping, setOtherTyping] = useState(false)
  const socket = useRef(null)
  const h = useRef(handlers)
  h.current = handlers
  const typingTimer = useRef(null)
  const lastTyping = useRef(0)

  useEffect(() => {
    if (!incidentId) return undefined
    const s = connectSocket(role)
    if (!s) return undefined
    socket.current = s
    const id = Number(incidentId)
    s.on('connect', () => s.emit('join_incident', { incident_id: id }))
    s.on('joined_incident', () => setConnected(true))
    s.on('join_denied', () => setConnected(false))
    s.on('disconnect', () => setConnected(false))
    s.on('chat:message', (m) => { if (m.incident_id === id) { setOtherTyping(false); h.current.onMessage?.(m) } })
    s.on('location:update', (p) => { if (p.incident_id === id) h.current.onLocation?.(p) })
    s.on('incident:update', (inc) => { if (inc.id === id) h.current.onIncident?.(inc) })
    s.on('typing', (d) => {
      if (d.incident_id !== id) return
      clearTimeout(typingTimer.current)
      setOtherTyping(d.is_typing !== false)
      typingTimer.current = setTimeout(() => setOtherTyping(false), 4000)
    })
    return () => {
      clearTimeout(typingTimer.current)
      s.disconnect()
      socket.current = null
      setConnected(false)
    }
  }, [role, incidentId])

  const notifyTyping = useCallback(() => {
    const now = Date.now()
    if (!socket.current?.connected || now - lastTyping.current < 2500) return
    lastTyping.current = now
    socket.current.emit('typing', { incident_id: Number(incidentId), is_typing: true })
  }, [incidentId])

  const stopTyping = useCallback(() => {
    lastTyping.current = 0
    socket.current?.emit('typing', { incident_id: Number(incidentId), is_typing: false })
  }, [incidentId])

  return { connected, otherTyping, notifyTyping, stopTyping }
}
