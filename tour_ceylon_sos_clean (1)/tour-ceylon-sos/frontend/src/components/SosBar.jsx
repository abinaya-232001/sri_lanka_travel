import { useState } from 'react'
import { Mic, Siren, Square, X } from 'lucide-react'
import useVoiceRecorder from '../hooks/useVoiceRecorder'

/**
 * Type what is happening, then press SOS.
 * The message is classified into an incident type, with tips, numbers, and the nearest station.
 */
export default function SosBar({ language, sending, hasOpenCase, onSend }) {
  const [text, setText] = useState('')
  const voice = useVoiceRecorder(language)

  const press = async () => {
    if (sending || voice.recording) return
    const ok = await onSend({ message: text.trim(), voice: voice.blob, transcript: voice.transcript, extension: voice.extension })
    if (ok) { setText(''); voice.reset() }
  }

  return (
    <section className="sos-panel" aria-label="Emergency SOS">
      <div className="sos-row">
        <div className={`sos-field${voice.recording ? ' recording' : ''}`}>
          <input
            value={voice.recording ? '' : text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); press() } }}
            placeholder={voice.recording ? `Listening… ${voice.seconds}s` : hasOpenCase ? 'Add what is happening' : 'What is happening?'}
            aria-label="Describe your emergency"
            disabled={voice.recording || sending}
          />
          <button type="button" className={`mic${voice.recording ? ' on' : ''}`} disabled={sending}
            onClick={voice.recording ? voice.stop : voice.start}
            aria-label={voice.recording ? 'Stop recording' : 'Record a voice message'}>
            {voice.recording ? <Square size={16} fill="currentColor" /> : <Mic size={19} />}
          </button>
        </div>
        <button type="button" className="sos-btn" onClick={press} disabled={sending || voice.recording} aria-label="Send SOS">
          <Siren size={18} /> {sending ? 'Sending' : 'Send SOS'}
        </button>
      </div>

      {voice.recording && voice.transcript && <p className="sos-note">“{voice.transcript}”</p>}
      {voice.blob && !voice.recording && (
        <div className="voice-ready">
          <Mic size={16} />
          <span className="grow"><b>Voice note ready.</b>{' '}
            <span className="muted">{voice.transcript ? `“${voice.transcript}”` : 'It will be added to your message after you send.'}</span>
          </span>
          <button type="button" className="icon-btn" style={{ width: 32, height: 32 }} onClick={voice.reset} aria-label="Delete voice message"><X size={15} /></button>
        </div>
      )}
      {voice.error && <p className="error" role="alert">{voice.error}</p>}
      <p className="sos-note">
        {hasOpenCase
          ? 'This case is open. A new message updates the incident type, the numbers, and the station.'
          : 'Your message sets the incident type. You get the matching tips and phone numbers, and the nearest police station is alerted.'}
      </p>
    </section>
  )
}
