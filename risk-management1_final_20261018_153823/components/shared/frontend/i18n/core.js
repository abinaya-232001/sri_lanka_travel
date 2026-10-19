import { SITE_LANGUAGES } from './languages.js'
import { messages, translate } from './messages.js'

const STORAGE_KEY = 'siteLanguage'
const LEGACY_SOS_KEY = 'sosLang'
export const SITE_LANGUAGE_EVENT = 'site-language-change'

/** Tour Ceylon UI is English-only for now. */
const FIXED_LANGUAGE = 'en'

export { SITE_LANGUAGES, translate, messages }

export function getSiteLanguage() {
  return FIXED_LANGUAGE
}

export function setSiteLanguage(_language) {
  localStorage.setItem(STORAGE_KEY, FIXED_LANGUAGE)
  localStorage.setItem(LEGACY_SOS_KEY, FIXED_LANGUAGE)
  document.documentElement.lang = FIXED_LANGUAGE
  window.dispatchEvent(new CustomEvent(SITE_LANGUAGE_EVENT, { detail: FIXED_LANGUAGE }))
  return FIXED_LANGUAGE
}

/** Non-reactive helper (prefer useSiteI18n in React components). */
export function t(key, language = getSiteLanguage()) {
  return translate(key, language)
}

export function getLang() {
  return getSiteLanguage()
}

export function setLang(language) {
  return setSiteLanguage(language)
}

export const LANGS = SITE_LANGUAGES.map(([code]) => code)
