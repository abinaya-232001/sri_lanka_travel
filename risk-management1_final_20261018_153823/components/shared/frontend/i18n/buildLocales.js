/**
 * Builds complete locale objects: every language gets every key from English,
 * with translated values where provided in overrides.
 */
import { EN } from './messages.js'

const LANGS = ['si', 'ta', 'ru', 'de', 'zh', 'ja', 'es', 'fr', 'ko']

/** Apply overrides on top of English so no key is ever missing. */
export function completeLocale(overrides = {}) {
  return { ...EN, ...overrides }
}

/** SOS emergency type labels — key pattern sosType_{id} and sosType_{id}_short */
export function sosTypeKeys() {
  const ids = [
    'general', 'medical', 'accident', 'hospital_assistance', 'police_assistance',
    'harassment', 'theft', 'rape', 'lost_passport', 'missing_person', 'fire',
    'natural_disaster', 'cybercrime', 'financial_fraud', 'unsafe_location', 'other',
  ]
  const labels = {
    general: ['General Emergency', 'General'],
    medical: ['Medical Emergency', 'Medical'],
    accident: ['Road Accident', 'Accident'],
    hospital_assistance: ['Hospital Assistance', 'Hospital'],
    police_assistance: ['Police Assistance', 'Police'],
    harassment: ['Harassment', 'Harassment'],
    theft: ['Theft', 'Theft'],
    rape: ['Assault', 'Assault'],
    lost_passport: ['Lost Passport', 'Passport'],
    missing_person: ['Missing Person', 'Missing'],
    fire: ['Fire', 'Fire'],
    natural_disaster: ['Natural Disaster', 'Disaster'],
    cybercrime: ['Cybercrime', 'Cyber'],
    financial_fraud: ['Financial Fraud', 'Fraud'],
    unsafe_location: ['Unsafe Location', 'Unsafe'],
    other: ['Other Emergency', 'Other'],
  }
  const keys = {}
  ids.forEach((id) => {
    keys[`sosType_${id}`] = labels[id][0]
    keys[`sosType_${id}_short`] = labels[id][1]
  })
  return keys
}

Object.assign(EN, sosTypeKeys())

export { EN, LANGS }
