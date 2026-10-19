import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { errorText, session, touristApi } from '../api'

const LANGUAGES = [['en', 'English'], ['de', 'Deutsch'], ['fr', 'Français'], ['es', 'Español'], ['it', 'Italiano'],
  ['ru', 'Русский'], ['zh', '中文'], ['ja', '日本語'], ['ko', '한국어'], ['hi', 'हिन्दी'], ['ar', 'العربية'], ['nl', 'Nederlands'], ['si', 'සිංහල'], ['ta', 'தமிழ்']]

export default function AuthPage() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('login')
  const [f, setF] = useState({ name: '', email: '', password: '', phone: '', nationality: '', language: 'en' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const url = mode === 'login' ? '/api/auth/tourist/login' : '/api/auth/tourist/register'
      const body = mode === 'login' ? { email: f.email, password: f.password } : f
      const { data } = await touristApi.post(url, body)
      session.set('tourist', data.token)
      navigate(mode === 'login' ? '/' : '/safety-card')
    } catch (err) { setError(errorText(err)) } finally { setBusy(false) }
  }

  return (
    <main className="auth">
      <h1>{mode === 'login' ? 'Sign in' : 'Create your account'}</h1>
      <p className="lede">Emergency assistance for visitors in Sri Lanka. Police, location sharing, and family alerts in one place.</p>
      <form className="card auth-card" onSubmit={submit}>
        <div className="seg" role="tablist">
          <button type="button" className={mode === 'login' ? 'on' : ''} onClick={() => setMode('login')}>Sign in</button>
          <button type="button" className={mode === 'register' ? 'on' : ''} onClick={() => setMode('register')}>Create account</button>
        </div>
        {mode === 'register' && <label className="label">Full name<input className="field" required value={f.name} onChange={set('name')} autoComplete="name" /></label>}
        <label className="label">Email<input className="field" type="email" required value={f.email} onChange={set('email')} autoComplete="email" /></label>
        <label className="label">Password<input className="field" type="password" required minLength={8} value={f.password} onChange={set('password')}
          autoComplete={mode === 'login' ? 'current-password' : 'new-password'} /></label>
        {mode === 'register' && (
          <>
            <label className="label">Your phone (with country code)<input className="field" value={f.phone} onChange={set('phone')} placeholder="+44 7700 900123" autoComplete="tel" /></label>
            <label className="label">Nationality<input className="field" value={f.nationality} onChange={set('nationality')} /></label>
            <label className="label">Language you speak
              <select className="field" value={f.language} onChange={set('language')}>{LANGUAGES.map(([c, n]) => <option key={c} value={c}>{n}</option>)}</select>
            </label>
          </>
        )}
        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn btn-primary" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}</button>
      </form>
      <p className="auth-foot">Station officer? <Link to="/police/login">Station sign in</Link></p>
    </main>
  )
}
