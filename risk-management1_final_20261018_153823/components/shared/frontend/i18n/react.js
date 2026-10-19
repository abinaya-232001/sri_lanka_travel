import { useCallback, useEffect, useState } from 'react'
import {
  getSiteLanguage,
  setSiteLanguage,
  SITE_LANGUAGE_EVENT,
  SITE_LANGUAGES,
  translate,
} from './core.js'

export {
  getSiteLanguage,
  setSiteLanguage,
  SITE_LANGUAGE_EVENT,
  SITE_LANGUAGES,
  translate,
  messages,
  t,
  getLang,
  setLang,
  LANGS,
} from './core.js'

/** Reactive hook for any tourist-facing React page or shared chrome. */
export function useSiteI18n() {
  const [language, setLanguageState] = useState(getSiteLanguage)

  useEffect(() => {
    document.documentElement.lang = language === 'zh' ? 'zh-Hans' : language
    const onChange = (event) => setLanguageState(event.detail || getSiteLanguage())
    window.addEventListener(SITE_LANGUAGE_EVENT, onChange)
    return () => window.removeEventListener(SITE_LANGUAGE_EVENT, onChange)
  }, [language])

  const t = useCallback((key) => translate(key, language), [language])

  return {
    language,
    languages: SITE_LANGUAGES,
    setLanguage: (next) => setSiteLanguage(next),
    t,
  }
}
