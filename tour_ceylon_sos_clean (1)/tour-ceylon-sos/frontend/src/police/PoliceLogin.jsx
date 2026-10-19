import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorText, policeApi, session } from '../api'

export default function PoliceLogin() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const { data } = await policeApi.post('/api/auth/police/login', { username, password })
      session.set('police', data.token)
      navigate('/police')
    } catch (err) { setError(errorText(err)) } finally { setBusy(false) }
  }

  return (
    <main className="desk-auth">
      <section className="desk-auth-side">
        <a className="auth-mark" href="http://127.0.0.1:5000/#/home"><img src="/logo.png" alt="" /> TourCeylon</a>
        <div>
          <p className="eyebrow">Station operations</p>
          <h1>Police desk</h1>
          <p>Assigned cases, live location, and direct contact with the visitor. Officers see only the cases for their station.</p>
        </div>
      </section>
      <section className="desk-auth-form">
        <form className="card auth-card" onSubmit={submit}>
          <h1>Sign in</h1>
          <p className="lede">Use the username issued to your station.</p>
          <label className="label">Station username<input className="field" required value={username} onChange={(e) => setUsername(e.target.value)} placeholder="seeduwa-police" autoComplete="username" /></label>
          <label className="label">Password<input className="field" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" /></label>
          {error && <p className="error" role="alert">{error}</p>}
          <button className="btn btn-primary" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
          <p className="auth-foot"><a href="http://127.0.0.1:5000/#/home">Return to TourCeylon</a></p>
        </form>
      </section>
    </main>
  )
}
