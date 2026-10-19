import { io } from 'socket.io-client'
import { API_URL, session } from './api'

export function connectSocket(role) {
  const token = session.get(role)
  if (!token) return null
  return io(API_URL || window.location.origin, {
    transports: ['websocket', 'polling'],
    query: { token },
    reconnection: true,
    reconnectionAttempts: Infinity,
    reconnectionDelayMax: 10000,
  })
}
