import { useCallback, useEffect, useRef, useState } from 'react'

const MAX_SECONDS = 60
const CAN_TRANSCRIBE = typeof window !== 'undefined' && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
const SPEECH_LANG = { en: 'en-US', si: 'si-LK', ta: 'ta-IN', de: 'de-DE', fr: 'fr-FR', es: 'es-ES', it: 'it-IT',
  ru: 'ru-RU', zh: 'zh-CN', ja: 'ja-JP', ko: 'ko-KR', hi: 'hi-IN', ar: 'ar-SA', nl: 'nl-NL', pt: 'pt-PT' }

/**
 * Records a voice note (MediaRecorder) and, where the browser supports it,
 * shows a live transcript (Web Speech API). The server turns it into English.
 */
export default function useVoiceRecorder(language = 'en') {
  const [recording, setRecording] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [blob, setBlob] = useState(null)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState('')
  const recorder = useRef(null)
  const stream = useRef(null)
  const chunks = useRef([])
  const recognition = useRef(null)
  const timer = useRef(null)
  const text = useRef('')

  const cleanup = useCallback(() => {
    clearInterval(timer.current)
    try { recognition.current?.stop() } catch { /* ignore */ }
    recognition.current = null
    stream.current?.getTracks().forEach((t) => t.stop())
    stream.current = null
  }, [])

  useEffect(() => () => {
    if (recorder.current?.state === 'recording') try { recorder.current.stop() } catch { /* ignore */ }
    cleanup()
  }, [cleanup])

  const stop = useCallback(() => {
    const r = recorder.current
    if (!r || r.state !== 'recording') return
    r.onstop = () => {
      const b = new Blob(chunks.current, { type: r.mimeType || 'audio/webm' })
      cleanup()
      setRecording(false)
      if (b.size > 0) setBlob(b)
      else setError('Recording failed — please try again.')
    }
    try { r.stop() } catch { cleanup(); setRecording(false) }
  }, [cleanup])

  const start = useCallback(async () => {
    setError(''); setBlob(null); setTranscript(''); text.current = ''
    try {
      stream.current = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
      const mime = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4'].find((m) => window.MediaRecorder?.isTypeSupported?.(m))
      const r = new MediaRecorder(stream.current, mime ? { mimeType: mime } : undefined)
      chunks.current = []
      r.ondataavailable = (e) => { if (e.data?.size) chunks.current.push(e.data) }
      recorder.current = r
      r.start(250)
      setRecording(true)
      setSeconds(0)
      timer.current = setInterval(() => setSeconds((s) => {
        if (s + 1 >= MAX_SECONDS) stop()
        return s + 1
      }), 1000)
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition
      if (SR) {
        const rec = new SR()
        rec.continuous = true
        rec.interimResults = true
        rec.lang = SPEECH_LANG[language] || language || 'en-US'
        rec.onresult = (e) => {
          const said = Array.from(e.results).map((res) => res[0]?.transcript || '').join(' ').trim()
          if (said) { text.current = said; setTranscript(said) }
        }
        rec.onerror = () => {}
        recognition.current = rec
        try { rec.start() } catch { /* transcript preview is optional */ }
      }
    } catch {
      cleanup()
      setRecording(false)
      setError('Microphone permission is needed to record. You can type instead.')
    }
  }, [cleanup, language, stop])

  const reset = useCallback(() => { setBlob(null); setTranscript(''); text.current = ''; setError('') }, [])

  return { recording, seconds, blob, transcript, error, start, stop, reset,
    canTranscribe: CAN_TRANSCRIBE, extension: blob?.type.includes('mp4') ? 'm4a' : 'webm' }
}
