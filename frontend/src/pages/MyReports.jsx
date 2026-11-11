import { useEffect, useState } from 'react'
import { api } from '../api'
import { DetectionCard, Empty, Photo, Progress, RiskChip, StatusChip, ago } from '../components/ui'

export default function MyReports() {
  const [rows, setRows] = useState(null)
  const [err, setErr] = useState('')
  useEffect(() => {
    api('/api/reports').then(setRows).catch((e) => setErr(e.message))
  }, [])

  return (
    <section className="card">
      <h1>My reports</h1>
      <p className="err">{err}</p>
      {rows === null ? <p className="muted">Loading…</p> : rows.length === 0 ? (
        <Empty title="No reports yet" text="Your reports and their cleanup progress appear here." />
      ) : rows.map((r) => (
        <article key={r.id} className="task">
          <div className="side">
            <Photo src={r.photo_url} caption="Before" />
            {r.after_photo_url && <Photo src={r.after_photo_url} caption="After" />}
          </div>
          <div className="mainc">
            <div className="cardhead"><h3>Ward {r.ward_id} · {r.ward_name}</h3><div className="chips"><RiskChip risk={r.risk} /><StatusChip status={r.status} /></div></div>
            <p className="muted small">Sent {ago(r.created_at)}{r.confirmations > 1 ? ` · ${r.confirmations} people reported this spot` : ''}</p>
            <DetectionCard d={r.detection} />
            <Progress r={r} />
          </div>
        </article>
      ))}
    </section>
  )
}
