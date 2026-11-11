import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import MapView from '../components/MapView'
import { DetectionCard, Empty, Photo, Progress, RiskCard, RiskChip, StatusChip, ago } from '../components/ui'

const ORDER = { open: 0, cleaned: 1, assigned: 2, closed: 3 }
const REFRESH_MS = 15000

export default function Officer() {
  const [reports, setReports] = useState([])
  const [wards, setWards] = useState([])
  const [forecast, setForecast] = useState([])
  const [workers, setWorkers] = useState([])
  const [stats, setStats] = useState(null)
  const [selId, setSelId] = useState(null)
  const [filter, setFilter] = useState('active')
  const [err, setErr] = useState('')

  const load = useCallback(async () => {
    try {
      const [r, w, f, a] = await Promise.all([api('/api/reports'), api('/api/wards'), api('/api/forecast'), api('/api/analytics')])
      setReports(r); setWards(w); setForecast(f); setStats(a); setErr('')
    } catch (e) {
      setErr(e.message)
    }
  }, [])

  useEffect(() => {
    load()
    api('/api/workers').then(setWorkers).catch(() => {})
    const t = setInterval(load, REFRESH_MS)
    return () => clearInterval(t)
  }, [load])

  const sorted = [...reports]
    .filter((r) => filter === 'all' || r.status !== 'closed')
    .sort((a, b) => ORDER[a.status] - ORDER[b.status] || b.risk.score - a.risk.score)
  const sel = reports.find((r) => r.id === selId)

  const act = async (path, body) => {
    try {
      const updated = await api(path, { method: 'POST', body })
      setReports((rs) => rs.map((r) => (r.id === updated.id ? updated : r)))
      load()
    } catch (e) {
      setErr(e.message)
    }
  }

  return (
    <>
      <div className="stats">
        <div className="stat"><b>{stats?.by_status.open ?? '–'}</b><span>New, not assigned</span></div>
        <div className={`stat ${stats?.high_risk_open ? 'alert' : ''}`}><b>{stats?.high_risk_open ?? '–'}</b><span>High risk, still open</span></div>
        <div className="stat"><b>{stats ? stats.by_status.assigned + stats.by_status.cleaned : '–'}</b><span>With field workers</span></div>
        <div className="stat"><b>{stats?.by_status.closed ?? '–'}</b><span>Closed{stats?.avg_hours_to_close != null ? ` · avg ${stats.avg_hours_to_close} h` : ''}</span></div>
      </div>
      {err && <p className="err">{err}</p>}

      <div className="grid2 off">
        <section className="card">
          <div className="cardhead">
            <h2>Hotspot map</h2>
            <div className="legend"><span><i className="High" />High</span><span><i className="Medium" />Medium</span><span><i className="Low" />Low</span><span><i className="Closed" />Closed</span></div>
          </div>
          <MapView reports={sorted} wards={wards} selectedId={selId} onSelect={setSelId} focus={sel} height={420} />

          <h3 className="sub">7-day hotspot outlook</h3>
          <div className="tablewrap"><table>
            <thead><tr><th>Ward</th><th>Rain next 7 days</th><th>Reports</th><th>Outlook</th></tr></thead>
            <tbody>{forecast.map((f) => (
              <tr key={f.ward_id}><td>{f.ward_id} · {f.ward_name}</td><td>{f.rain_next_7d_mm} mm</td><td>{f.reports}</td><td><span className={`chip ${f.level}`}>{f.level} {f.score}</span></td></tr>
            ))}</tbody>
          </table></div>

          <h3 className="sub">Ward conditions <span className="tag">sample data</span></h3>
          <div className="tablewrap"><table>
            <thead><tr><th>Ward</th><th>Rain, last 7 days</th><th>Dengue cases</th><th>Open</th><th>Top risk</th></tr></thead>
            <tbody>{wards.map((w) => (
              <tr key={w.id}><td>{w.id} · {w.name}</td><td>{w.rain_7d_mm} mm</td><td>{w.dengue_cases_30d}</td><td>{w.open_reports}</td><td>{w.top_risk ? <span className={`chip ${w.top_risk}`}>{w.top_risk}</span> : '–'}</td></tr>
            ))}</tbody>
          </table></div>
        </section>

        <div className="col">
          {sel && <Detail r={sel} workers={workers} act={act} close={() => setSelId(null)} />}
          <section className="card">
            <div className="cardhead">
              <h2>Reports</h2>
              <select value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter reports">
                <option value="active">Open and in progress</option>
                <option value="all">All, including closed</option>
              </select>
            </div>
            {sorted.length === 0 ? <Empty title="No reports" text="New reports from residents appear here." /> : (
              <div className="list">{sorted.map((r) => (
                <button key={r.id} className="item" aria-current={r.id === selId} onClick={() => { setSelId(r.id); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>
                  <img className="th" src={r.photo_url} alt="" />
                  <span className="mid">
                    <span className="t">Ward {r.ward_id} · {r.ward_name}</span>
                    <span className="s">{r.detection.objects?.map((o) => o.label).join(', ') || r.detection.summary}</span>
                    <span className="s">{ago(r.created_at)}{r.confirmations > 1 ? ` · ${r.confirmations} reports` : ''}</span>
                  </span>
                  <span className="r"><RiskChip risk={r.risk} /><StatusChip status={r.status} /></span>
                </button>
              ))}</div>
            )}
          </section>
        </div>
      </div>
    </>
  )
}

function Detail({ r, workers, act, close }) {
  const [worker, setWorker] = useState('')
  useEffect(() => setWorker(workers[0]?.id ?? ''), [workers, r.id])
  return (
    <section className="card" aria-label="Report details">
      <div className="cardhead"><h2>Ward {r.ward_id} · {r.ward_name}</h2><button className="btn small" onClick={close}>Close</button></div>
      <div className="chips"><StatusChip status={r.status} /><span className="chip st">{ago(r.created_at)}</span><span className="chip st">by {r.reporter_name}</span></div>
      <div className="photos">
        <Photo src={r.photo_url} caption="Before" />
        {r.after_photo_url && <Photo src={r.after_photo_url} caption="After" />}
      </div>
      {r.note && <p className="note">“{r.note}”</p>}
      <DetectionCard d={r.detection} />
      <RiskCard risk={r.risk} />
      <Progress r={r} />
      <div className="actions">
        {r.status === 'open' && (
          <>
            <label htmlFor="assignTo">Send to</label>
            <select id="assignTo" value={worker} onChange={(e) => setWorker(Number(e.target.value))}>
              {workers.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>
            <button className="btn primary small" disabled={!worker} onClick={() => act(`/api/reports/${r.id}/assign`, { worker_id: Number(worker) })}>Assign</button>
          </>
        )}
        {r.status === 'assigned' && <span className="muted small">Waiting for {r.assigned_to?.name} to clean it and upload proof.</span>}
        {r.status === 'cleaned' && (
          <>
            <span className="muted small">Compare the photos, then:</span>
            <button className="btn primary small" onClick={() => act(`/api/reports/${r.id}/verify`, { approve: true })}>Verify and close</button>
            <button className="btn small" onClick={() => act(`/api/reports/${r.id}/verify`, { approve: false })}>Send back</button>
          </>
        )}
        {r.status === 'closed' && <span className="muted small">Closed {ago(r.closed_at)}.</span>}
      </div>
    </section>
  )
}
