/** Browser speech-to-text language codes for SOS voice (11 tourist languages). */
export const VOICE_STT_LANG = {
  en: 'en-US',
  si: 'si-LK',
  ta: 'ta-IN',
  ru: 'ru-RU',
  de: 'de-DE',
  zh: 'zh-CN',
  ja: 'ja-JP',
  es: 'es-ES',
  fr: 'fr-FR',
  ko: 'ko-KR',
  ar: 'ar-SA',
}

export const VOICE_UI_LANGUAGES = Object.keys(VOICE_STT_LANG)

export const VOICE_LANGUAGE_OPTIONS = [
  ['si', 'Sinhala'],
  ['ta', 'Tamil'],
  ['en', 'English'],
  ['ru', 'Russian'],
  ['de', 'German'],
  ['zh', 'Chinese'],
  ['ja', 'Japanese'],
  ['es', 'Spanish'],
  ['fr', 'French'],
  ['ko', 'Korean'],
  ['ar', 'Arabic'],
]

export const VOICE_LANGUAGE_KEY = 'voiceLanguage'
const LEGACY_SOS_KEY = 'sosLang'

const ENGLISH_EMERGENCY = /\b(help|please|police|emergency|hospital|fire|accident|robbery|stolen|hurt|injured|scared|save|rescue|hello|hi|need|urgent|call|danger|attack|theft|medical|ambulance|someone|following|lost|unsafe)\b/i

const LANGUAGE_HINTS = [
  ['si', /[\u0D80-\u0DFF]/],
  ['ta', /[\u0B80-\u0BFF]/],
  ['zh', /[\u4E00-\u9FFF]/],
  ['ja', /[\u3040-\u30FF\u4E00-\u9FFF]/],
  ['ko', /[\uAC00-\uD7AF]/],
  ['ru', /[\u0400-\u04FF]/],
  ['ar', /[\u0600-\u06FF]/],
  ['de', /\b(hilfe|notfall|polizei|krankenhaus|bitte|angst|folgt|rettung|retten)\b/i],
  ['es', /\b(ayuda|emergencia|polic[ií]a|hospital|por favor|socorro)\b/i],
  ['fr', /\b(aide|urgence|police|h[ôo]pital|s'il vous pla[iî]t|au secours)\b/i],
]

export function languageLabel(code) {
  const key = String(code || '').split('-')[0].toLowerCase()
  return VOICE_LANGUAGE_OPTIONS.find(([value]) => value === key)?.[1] || 'Sinhala'
}

export function mergeRecognitionResults(results, { finalsOnly = false } = {}) {
  if (!results?.length) return ''
  let finals = ''
  let interim = ''
  for (let i = 0; i < results.length; i += 1) {
    const piece = results[i][0]?.transcript || ''
    if (results[i].isFinal) finals += piece
    else interim = piece
  }
  if (finalsOnly) return finals.replace(/\s+/g, ' ').trim()
  return `${finals} ${interim}`.replace(/\s+/g, ' ').trim()
}

function normalizeVoiceCode(code) {
  const key = String(code || '').split('-')[0].toLowerCase()
  return VOICE_UI_LANGUAGES.includes(key) ? key : null
}

export function isLikelyMisheardEnglish(text) {
  const sample = String(text || '').trim()
  if (!sample || sample.length < 3) return false
  for (const [, pattern] of LANGUAGE_HINTS) {
    if (pattern.test(sample)) return false
  }
  if (/[^\u0000-\u007F]/.test(sample)) return false
  if (ENGLISH_EMERGENCY.test(sample)) return false
  return true
}

export function detectLanguageFromText(text) {
  const sample = String(text || '').trim()
  if (!sample) return null
  for (const [code, pattern] of LANGUAGE_HINTS) {
    if (pattern.test(sample)) return code
  }
  if (isLikelyMisheardEnglish(sample)) return null
  return 'en'
}

export function setVoiceLanguage(code) {
  const normalized = normalizeVoiceCode(code)
  if (!normalized) return 'si'
  try {
    localStorage.setItem(VOICE_LANGUAGE_KEY, normalized)
    localStorage.setItem(LEGACY_SOS_KEY, normalized)
  } catch {
    /* ignore */
  }
  return normalized
}

/** Only explicit voice picker / saved voice language — never profile English default. */
export function getVoiceLanguage() {
  try {
    for (const key of [VOICE_LANGUAGE_KEY, LEGACY_SOS_KEY]) {
      const stored = normalizeVoiceCode(localStorage.getItem(key))
      if (stored) return stored
    }
  } catch {
    /* ignore */
  }
  return 'si'
}

export function resolveVoiceLanguage(preferred) {
  const explicit = normalizeVoiceCode(preferred)
  if (explicit) return explicit
  return getVoiceLanguage()
}

/**
 * Optional browser captions for the selected language only.
 * Chrome on Windows often fails for Sinhala — server STT is the source of truth.
 */
export function startFixedLanguageSpeechRecognition(languageCode, onTranscript) {
  const SpeechRecognition = typeof window !== 'undefined'
    && (window.SpeechRecognition || window.webkitSpeechRecognition)
  if (!SpeechRecognition) return null

  const lang = resolveVoiceLanguage(languageCode)
  const recognition = new SpeechRecognition()
  recognition.continuous = true
  recognition.interimResults = true
  recognition.maxAlternatives = 1
  recognition.lang = VOICE_STT_LANG[lang] || VOICE_STT_LANG.si
  recognition.onresult = (event) => {
    const text = mergeRecognitionResults(event.results)
    if (text) onTranscript(text)
  }
  recognition.onerror = () => {}
  recognition.onend = () => {
    try { recognition.start() } catch { /* ignore */ }
  }

  try {
    recognition.start()
  } catch {
    return null
  }

  return () => {
    try { recognition.onend = null } catch { /* ignore */ }
    try { recognition.stop() } catch { /* ignore */ }
  }
}

export function startBrowserSpeechRecognition(languageCode, onTranscript) {
  return startFixedLanguageSpeechRecognition(languageCode, onTranscript)
}

export function startAdaptiveSpeechRecognition({ initialLang, onTranscript, onLanguageDetected }) {
  const lang = resolveVoiceLanguage(initialLang)
  onLanguageDetected?.(lang)
  return startFixedLanguageSpeechRecognition(lang, onTranscript)
}
