import { useEffect, useRef, useState } from 'react'
import './ChatMedia.css'

export const CHAT_VOICE_WIDTH = 220
export const CHAT_PHOTO_SIZE = 220

/** Same bar heights on every note so short and long recordings look identical. */
const WAVE_BARS = [7, 14, 9, 18, 11, 16, 8, 20, 12, 17, 10, 19, 9, 15, 13, 18, 8, 14]

const VOICE_NOTE_STYLE = {
  width: CHAT_VOICE_WIDTH,
  minWidth: CHAT_VOICE_WIDTH,
  maxWidth: CHAT_VOICE_WIDTH,
  height: 52,
  boxSizing: 'border-box',
  display: 'flex',
  alignItems: 'center',
  gap: 8,
  padding: '6px 8px',
  borderRadius: 8,
  background: 'rgba(8, 32, 38, 0.07)',
  flexShrink: 0,
  overflow: 'hidden',
}

const WAVE_STYLE = {
  width: 120,
  minWidth: 120,
  maxWidth: 120,
  height: 22,
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  flexShrink: 0,
}

function formatClock(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00'
  const total = Math.floor(seconds)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

export function ChatVoiceNote({ src }) {
  const audioRef = useRef(null)
  const [playing, setPlaying] = useState(false)
  const [duration, setDuration] = useState(0)
  const [current, setCurrent] = useState(0)

  useEffect(() => {
    const el = audioRef.current
    if (!el) return undefined
    setPlaying(false)
    setCurrent(0)
    setDuration(0)

    const onMeta = () => setDuration(Number.isFinite(el.duration) ? el.duration : 0)
    const onTime = () => setCurrent(el.currentTime || 0)
    const onEnd = () => {
      setPlaying(false)
      setCurrent(0)
    }
    el.addEventListener('loadedmetadata', onMeta)
    el.addEventListener('durationchange', onMeta)
    el.addEventListener('timeupdate', onTime)
    el.addEventListener('ended', onEnd)
    return () => {
      el.pause()
      el.removeEventListener('loadedmetadata', onMeta)
      el.removeEventListener('durationchange', onMeta)
      el.removeEventListener('timeupdate', onTime)
      el.removeEventListener('ended', onEnd)
    }
  }, [src])

  const toggle = () => {
    const el = audioRef.current
    if (!el) return
    if (playing) {
      el.pause()
      setPlaying(false)
      return
    }
    el.play()
      .then(() => setPlaying(true))
      .catch(() => setPlaying(false))
  }

  const progress = duration > 0 ? Math.min(1, current / duration) : 0

  return (
    <div className="sos-voice-note" style={VOICE_NOTE_STYLE}>
      <audio ref={audioRef} src={src} preload="metadata" />
      <button
        type="button"
        className="sos-voice-note-play"
        onClick={toggle}
        aria-label={playing ? 'Pause voice message' : 'Play voice message'}
        style={{
          width: 36,
          height: 36,
          minWidth: 36,
          border: 'none',
          borderRadius: '50%',
          background: '#0a4a52',
          color: '#fff',
          flexShrink: 0,
          cursor: 'pointer',
          display: 'grid',
          placeItems: 'center',
          padding: 0,
        }}
      >
        {playing ? (
          <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
            <rect x="2" y="2" width="3.5" height="10" rx="0.6" fill="currentColor" />
            <rect x="8.5" y="2" width="3.5" height="10" rx="0.6" fill="currentColor" />
          </svg>
        ) : (
          <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
            <path d="M4 2.4v9.2l8-4.6-8-4.6z" fill="currentColor" />
          </svg>
        )}
      </button>
      <div className="sos-voice-note-wave" aria-hidden="true" style={WAVE_STYLE}>
        {WAVE_BARS.map((height, index) => (
          <span
            key={index}
            style={{
              width: 3,
              height,
              borderRadius: 2,
              background: '#0a4a52',
              display: 'block',
              flexShrink: 0,
              opacity: index / WAVE_BARS.length <= progress ? 1 : 0.32,
            }}
          />
        ))}
      </div>
      <span
        className="sos-voice-note-time"
        style={{
          width: 36,
          minWidth: 36,
          flexShrink: 0,
          fontSize: 11,
          lineHeight: 1,
          fontVariantNumeric: 'tabular-nums',
          color: '#667781',
          textAlign: 'right',
        }}
      >
        {formatClock(playing ? current : duration)}
      </span>
    </div>
  )
}

export function ChatPhoto({ src, alt = '', href }) {
  const img = (
    <img
      className="sos-chat-photo"
      src={src}
      alt={alt}
      style={{
        width: CHAT_PHOTO_SIZE,
        height: CHAT_PHOTO_SIZE,
        minWidth: CHAT_PHOTO_SIZE,
        minHeight: CHAT_PHOTO_SIZE,
        objectFit: 'cover',
        objectPosition: 'center',
        display: 'block',
        borderRadius: 8,
      }}
    />
  )
  if (!href) return img
  return (
    <a
      className="sos-chat-photo-link"
      href={href}
      target="_blank"
      rel="noreferrer"
      style={{
        display: 'block',
        width: CHAT_PHOTO_SIZE,
        height: CHAT_PHOTO_SIZE,
        overflow: 'hidden',
        borderRadius: 8,
        flexShrink: 0,
      }}
    >
      {img}
    </a>
  )
}
