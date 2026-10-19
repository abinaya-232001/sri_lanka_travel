import { ChatVoiceNote } from './ChatMedia'

const LANG_LABELS = {
  en: 'English',
  si: 'Sinhala',
  ta: 'Tamil',
  ru: 'Russian',
  de: 'German',
  zh: 'Chinese',
  ja: 'Japanese',
  es: 'Spanish',
  fr: 'French',
  ko: 'Korean',
}

const URL_PATTERN = /(https?:\/\/[^\s]+)/g

function langLabel(code) {
  if (!code) return 'Unknown'
  const key = String(code).toLowerCase().split('-')[0]
  return LANG_LABELS[key] || key.toUpperCase()
}

function touristOriginal(message) {
  if (message.tourist_body) return message.tourist_body
  if (message.message_type === 'voice') {
    return message.voice_transcription || message.body || ''
  }
  return message.body || ''
}

function hasLatin(text) {
  return /[A-Za-z]/.test(String(text || ''))
}

function hasNonLatinScript(text) {
  return /[\u0D80-\u0DFF\u0B80-\u0BFF\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF\u0400-\u04FF\u0600-\u06FF]/.test(String(text || ''))
}

const KNOWN_ENGLISH = {
  'මම අතරමං වෙලා ඉන්නේ': 'I am lost',
  'මම අතරමං වුණා': 'I got lost',
  'මම අතරමං': 'I am lost',
  'අතරමං වෙලා ඉන්නේ': 'I am lost',
  'හොරෙක් හොරෙක්': 'Thief! Thief!',
  'හොරෙක්': 'Thief',
  'හොරා': 'Thief',
  'ගිනි': 'Fire',
  'ගින්න': 'Fire',
  'මෙන්න ගිනි': 'Fire here',
  'ඉක්මනට': 'Quickly',
  'පුළුවන්': 'Possible',
  'මට උදව් කරන්න': 'Help me',
  'මාව හැප්පුනා': 'I was hit',
  'මාව තැල්ලුවා': 'They hit me',
  'සොරකම': 'Theft',
  'මංකොල්ල': 'Robbery',
  'මංකොල්ලක්': 'A robbery',
  'திருடன்': 'Thief',
  'திருடன் திருடன்': 'Thief! Thief!',
  'திருட்டு': 'Theft',
}

function foldSosText(text) {
  return String(text || '')
    .trim()
    .replace(/[!?.,;:]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

function collapseRepeats(text) {
  const parts = foldSosText(text).split(' ').filter(Boolean)
  const out = []
  parts.forEach((part) => {
    if (out[out.length - 1] !== part) out.push(part)
  })
  return out.join(' ')
}

export function englishFromOriginal(text) {
  const raw = foldSosText(text)
  const collapsed = collapseRepeats(raw)
  if (KNOWN_ENGLISH[raw]) return KNOWN_ENGLISH[raw]
  if (KNOWN_ENGLISH[collapsed]) return KNOWN_ENGLISH[collapsed]
  let best = ''
  let bestLen = 0
  Object.entries(KNOWN_ENGLISH).forEach(([key, value]) => {
    if (key.length > bestLen && (raw.includes(key) || collapsed.includes(key))) {
      best = value
      bestLen = key.length
    }
  })
  return best
}

function officerPrimary(message, viewLanguage = 'en') {
  const original = touristOriginal(message)
  const candidates = [message.authority_body, message.translated_body, message.authority].filter(Boolean)
  const english = candidates.find((text) => (
    hasLatin(text) && !hasNonLatinScript(text)
  ))
  if (english) return english
  if (viewLanguage === 'en' && message.translated_body && hasLatin(message.translated_body) && !hasNonLatinScript(message.translated_body)) {
    return message.translated_body
  }
  const known = englishFromOriginal(original)
  if (known) return known
  return english || (hasLatin(candidates[0]) ? candidates[0] : '') || candidates[0] || original
}

function renderLinkedText(text, linkStyle = {}) {
  if (!text) return null
  const parts = String(text).split(URL_PATTERN)
  return parts.map((part, index) => {
    if (/^https?:\/\//.test(part)) {
      return (
        <a
          key={`link-${index}`}
          href={part}
          target="_blank"
          rel="noreferrer"
          style={{
            color: '#0a4a52',
            fontWeight: 600,
            wordBreak: 'break-all',
            ...linkStyle,
          }}
        >
          Open map
        </a>
      )
    }
    return <span key={`text-${index}`}>{part}</span>
  })
}

export function ChatMessageContent({ message, viewerRole = 'tourist', viewLanguage = 'en', mediaSrc, linkStyle }) {
  const isTouristMsg = message.sender_role === 'tourist'
  const language = message.original_language || message.voice_transcription_language || 'en'
  const original = touristOriginal(message)

  if (viewerRole === 'tourist' && isTouristMsg) {
    return (
      <>
        {message.message_type === 'voice' && message.media_url && mediaSrc && (
          <div style={{ marginBottom: original ? 6 : 0 }}>
            <ChatVoiceNote src={mediaSrc(message.media_url)} />
          </div>
        )}
        {original && (
          <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.45, whiteSpace: 'pre-wrap' }}>
            {renderLinkedText(original, linkStyle)}
          </p>
        )}
      </>
    )
  }

  if (viewerRole === 'tourist' && !isTouristMsg) {
    const translated = message.translated_body
    const primary = translated || original
    return (
      <>
        {message.message_type === 'voice' && message.media_url && mediaSrc && (
          <div style={{ marginBottom: original ? 6 : 0 }}>
            <ChatVoiceNote src={mediaSrc(message.media_url)} />
          </div>
        )}
        <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.45, whiteSpace: 'pre-wrap' }}>
          {renderLinkedText(primary, linkStyle)}
        </p>
        {original && translated && translated !== original && (
          <p style={{ margin: '6px 0 0', fontSize: 11, color: '#667781' }}>Officer (English): {original}</p>
        )}
      </>
    )
  }

  if (viewerRole === 'officer' && isTouristMsg) {
    const original = touristOriginal(message)
    const englishCandidates = [
      message.authority_body,
      message.translated_body,
      message.authority,
      englishFromOriginal(original),
    ].filter(Boolean)
    const english = englishCandidates.find((text) => (
      hasLatin(text) && !hasNonLatinScript(text)
    )) || ''
    const sourceLabel = message.original_language_label || langLabel(language)
    const isNonEnglish = language !== 'en' || hasNonLatinScript(original)
    const showOriginal = Boolean(
      original
      && (
        message.show_original
        || (isNonEnglish && english)
        || (hasNonLatinScript(original) && english)
      )
      && original.trim().toLowerCase() !== (english || '').trim().toLowerCase()
    )

    return (
      <>
        {message.message_type === 'voice' && message.media_url && mediaSrc && (
          <div style={{ marginBottom: original ? 6 : 0 }}>
            <ChatVoiceNote src={mediaSrc(message.media_url)} />
          </div>
        )}
        {english ? (
          <>
            <p style={{ margin: 0, fontSize: 10, fontWeight: 800, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#667781' }}>
              English
            </p>
            <p style={{ margin: '4px 0 0', fontSize: 15, lineHeight: 1.55, whiteSpace: 'pre-wrap', fontWeight: 600 }}>
              {renderLinkedText(english, linkStyle)}
            </p>
          </>
        ) : isNonEnglish && original ? (
          <p style={{ margin: 0, fontSize: 12.5, lineHeight: 1.45, color: '#667781', fontStyle: 'italic' }}>
            English translation pending…
          </p>
        ) : null}
        {showOriginal && original && (
          <p style={{ margin: english ? '8px 0 0' : '0', fontSize: 12.5, lineHeight: 1.45, opacity: 0.78 }}>
            Original ({sourceLabel}): {original}
          </p>
        )}
        {!english && !isNonEnglish && original && (
          <p style={{ margin: 0, fontSize: 15, lineHeight: 1.55, whiteSpace: 'pre-wrap', fontWeight: 600 }}>
            {renderLinkedText(original, linkStyle)}
          </p>
        )}
      </>
    )
  }

  const translated = message.translated_body
  const primary = translated || original
  return (
    <>
      {message.message_type === 'voice' && message.media_url && mediaSrc && (
        <div style={{ marginBottom: primary ? 6 : 0 }}>
          <ChatVoiceNote src={mediaSrc(message.media_url)} />
        </div>
      )}
      <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.45, whiteSpace: 'pre-wrap' }}>
        {renderLinkedText(primary, linkStyle)}
      </p>
    </>
  )
}

export { langLabel, LANG_LABELS, renderLinkedText }
