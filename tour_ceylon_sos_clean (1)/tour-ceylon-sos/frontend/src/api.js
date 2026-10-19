import axios from 'axios'

export const API_URL = import.meta.env.VITE_API_URL || ''

/** Separate sessions: a tourist and an officer can be logged in on the same device. */
export const session = {
  get: (role) => localStorage.getItem(`${role}Token`),
  set: (role, token) => localStorage.setItem(`${role}Token`, token),
  clear: (role) => localStorage.removeItem(`${role}Token`),
}

export function apiFor(role) {
  const client = axios.create({ baseURL: API_URL, timeout: 30000 })
  client.interceptors.request.use((cfg) => {
    const token = session.get(role)
    if (token) cfg.headers.Authorization = `Bearer ${token}`
    return cfg
  })
  client.interceptors.response.use(undefined, (err) => {
    if (err?.response?.status === 401) {
      session.clear(role)
      const onPoliceLogin = window.location.pathname.includes('/police/login')
      if (role === 'police' ? !onPoliceLogin : !window.location.pathname.includes('/police')) {
        window.location.href = role === 'police' ? '/police/login' : 'http://127.0.0.1:5000/#/sos'
      }
    }
    return Promise.reject(err)
  })
  return client
}

export const touristApi = apiFor('tourist')
export const policeApi = apiFor('police')

export function errorText(err, fallback = 'Something went wrong. Check your connection.') {
  return err?.response?.data?.error || fallback
}

/** Photos and voice notes need the token in the URL because <img>/<audio> cannot send headers. */
export function mediaUrl(path, role) {
  if (!path) return null
  return `${API_URL}${path}?token=${encodeURIComponent(session.get(role) || '')}`
}
