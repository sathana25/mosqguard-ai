import { useState } from 'react'
import { useAuth } from '../auth'

const DEMO = [
  ['Resident', 'resident1', 'resident123'],
  ['Officer', 'officer1', 'officer123'],
  ['Field worker', 'worker1', 'worker123'],
]

export default function Login() {
  const { login, register } = useAuth()
  const [mode, setMode] = useState('login')
  const [f, setF] = useState({ username: '', password: '', name: '' })
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  const go = async (fn) => {
    setErr('')
    setBusy(true)
    try {
      await fn()
    } catch (e) {
      setErr(e.message)
    } finally {
      setBusy(false)
    }
  }
  const submit = (e) => {
    e.preventDefault()
    go(() => (mode === 'login' ? login(f.username, f.password) : register(f)))
  }
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  return (
    <div className="login">
      <section className="card">
        <div>
          <h1>{mode === 'login' ? 'Log in' : 'Create a resident account'}</h1>
          <p className="muted">Report stagnant water, track cleanup, and help stop dengue in your ward.</p>
        </div>
        <form onSubmit={submit} className="form">
          {mode === 'register' && (
            <label>Your name<input id="name" value={f.name} onChange={set('name')} required autoComplete="name" /></label>
          )}
          <label>Username<input id="username" value={f.username} onChange={set('username')} required autoComplete="username" /></label>
          <label>Password<input id="password" type="password" value={f.password} onChange={set('password')} required minLength={mode === 'register' ? 6 : 1} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} /></label>
          <button className="btn primary" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account'}</button>
          <p className="err" role="alert">{err}</p>
        </form>
        <button className="link" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
          {mode === 'login' ? 'New resident? Create an account' : 'Have an account? Log in'}
        </button>
      </section>
      <section className="card">
        <h2>Try the demo</h2>
        <p className="muted">One tap logs in as each role.</p>
        <div className="demo">
          {DEMO.map(([role, u, p]) => (
            <button key={u} className="btn" disabled={busy} onClick={() => go(() => login(u, p))}>
              <b>{role}</b><small>{u} / {p}</small>
            </button>
          ))}
        </div>
      </section>
    </div>
  )
}
