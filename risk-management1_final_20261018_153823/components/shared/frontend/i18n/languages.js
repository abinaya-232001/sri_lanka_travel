/** Supported tourist UI languages (matches backend chat translation set). */
export const SITE_LANGUAGES = [
  ['en', 'English'],
  ['si', 'සිංහල'],
  ['ta', 'தமிழ்'],
  ['ru', 'Русский'],
  ['de', 'Deutsch'],
  ['zh', '中文'],
  ['ja', '日本語'],
  ['es', 'Español'],
  ['fr', 'Français'],
  ['ko', '한국어'],
  ['ar', 'العربية'],
]

export const SITE_LANGUAGE_CODES = SITE_LANGUAGES.map(([code]) => code)

export function languageLabel(code) {
  return SITE_LANGUAGES.find(([value]) => value === code)?.[1] || 'English'
}
