import { Navigate, NavLink, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth'
import Login from './pages/Login'
import Report from './pages/Report'
import MyReports from './pages/MyReports'
import Officer from './pages/Officer'
import Worker from './pages/Worker'

const HOME = { resident: '/report', officer: '/officer', worker: '/tasks' }
const NAV = {
  resident: [['/report', 'Report a spot'], ['/my-reports', 'My reports']],
  officer: [['/officer', 'Dashboard']],
  worker: [['/tasks', 'My tasks']],
}

function Guard({ role, children }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (role && user.role !== role) return <Navigate to={HOME[user.role]} replace />
  return children
}

export default function App() {
  const { user, loading, logout } = useAuth()
  if (loading) return <div className="center muted">Loading…</div>

  return (
    <>
      <header className="top">
        <div className="wrap topin">
          <div className="brand">
            <img src="/favicon.svg" width="32" height="32" alt="" />
            <div>
              <b>MOSQGUARD AI</b>
              <small>Report it. Rank it. Clean it.</small>
            </div>
          </div>
          {user && (
            <nav className="nav">
              {NAV[user.role].map(([to, label]) => (
                <NavLink key={to} to={to}>{label}</NavLink>
              ))}
              <span className="who">{user.name} · {user.role}</span>
              <button className="btn small" onClick={logout}>Log out</button>
            </nav>
          )}
        </div>
      </header>
      <main className="wrap main">
        <Routes>
          <Route path="/login" element={user ? <Navigate to={HOME[user.role]} replace /> : <Login />} />
          <Route path="/report" element={<Guard role="resident"><Report /></Guard>} />
          <Route path="/my-reports" element={<Guard role="resident"><MyReports /></Guard>} />
          <Route path="/officer" element={<Guard role="officer"><Officer /></Guard>} />
          <Route path="/tasks" element={<Guard role="worker"><Worker /></Guard>} />
          <Route path="*" element={<Navigate to={user ? HOME[user.role] : '/login'} replace />} />
        </Routes>
      </main>
      <footer className="wrap foot">
        MOSQGUARD AI · AI Hackathon 2026. The AI flags <em>suspected</em> breeding sites only; a field worker always confirms.
        Ward rainfall and dengue figures are sample data unless a weather API key is configured.
      </footer>
    </>
  )
}
