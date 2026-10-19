/**
 * Parse API datetimes from the Flask backend.
 * Values are stored as UTC but often serialized without a "Z" suffix.
 */
export function parseApiDateTime(iso) {
  if (!iso) return null
  const value = String(iso).trim()
  if (!value) return null
  if (/^\d{4}-\d{2}-\d{2}T/.test(value) && !/[zZ]|[+-]\d{2}:\d{2}$/.test(value)) {
    return new Date(`${value}Z`)
  }
  return new Date(value)
}

export function formatTime(iso, options = {}) {
  const date = parseApiDateTime(iso)
  if (!date || Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', ...options })
}

export function formatDateTime(iso, options = {}) {
  const date = parseApiDateTime(iso)
  if (!date || Number.isNaN(date.getTime())) return ''
  return date.toLocaleString([], options)
}
