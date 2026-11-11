// Shared display pieces: chips, photos, AI result, risk score and progress.

export const STATUS = { open: 'New', assigned: 'Assigned', cleaned: 'Cleaned · verify', closed: 'Closed' }

export function ago(iso) {
  if (!iso) return ''
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (m < 1) return 'just now'
  if (m < 60) return `${m} min ago`
  const h = Math.round(m / 60)
  if (h < 24) return `${h} h ago`
  return `${Math.round(h / 24)} d ago`
}

export const RiskChip = ({ risk }) => (
  <span className={`chip ${risk.level}`}>{risk.level} {risk.score}</span>
)

export const StatusChip = ({ status }) => <span className={`chip st ${status}`}>{STATUS[status]}</span>

export const Photo = ({ src, caption }) => (
  <figure className="ph">
    {src ? <img src={src} alt={`${caption} photo`} loading="lazy" /> : <div className="noimg">No photo</div>}
    <figcaption>{caption}</figcaption>
  </figure>
)

export function DetectionCard({ d }) {
  if (!d) return null
  return (
    <div className="aibox">
      <div className="label">AI photo check · {d.engine}</div>
      <p>{d.summary}</p>
      {d.objects?.length > 0 && (
        <div className="chips">
          {d.objects.map((o, i) => (
            <span className="chip obj" key={i}>{o.label} {Math.round(o.confidence * 100)}%</span>
          ))}
        </div>
      )}
      <div className="meta">
        <span>confidence {Math.round((d.confidence || 0) * 100)}%</span>
        <span>water {d.water_visible ? 'seen' : 'not seen'}</span>
        <span>larvae {d.larvae_visible ? 'possible' : 'not seen'}</span>
      </div>
      <p className="fine">
        {d.suspected ? 'Suspected site. A field worker confirms it on the spot.' : 'Not flagged. An officer can still review it.'}
      </p>
    </div>
  )
}

export function RiskCard({ risk }) {
  if (!risk) return null
  return (
    <div className={`risk ${risk.level}`}>
      <div className="score"><b>{risk.score}</b><span>/ 100</span><span className="lvl">{risk.level} risk</span></div>
      <div className="bar"><i style={{ width: `${risk.score}%` }} /></div>
      <ul>{risk.reasons.map((r, i) => <li key={i}>{r}</li>)}</ul>
    </div>
  )
}

export function Progress({ r }) {
  const step = { open: 0, assigned: 1, cleaned: 2, closed: 3 }[r.status]
  const items = ['Reported', r.assigned_to ? `Assigned to ${r.assigned_to.name}` : 'Assigned', 'Cleaned', 'Verified · closed']
  return (
    <ol className="tl">
      {items.map((t, i) => <li key={t} className={i <= step ? 'done' : ''}>{t}</li>)}
    </ol>
  )
}

export const Empty = ({ title, text }) => (
  <div className="empty"><b>{title}</b>{text}</div>
)
