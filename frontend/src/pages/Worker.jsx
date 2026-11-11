import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import MapView from '../components/MapView'
import { Empty, Photo, RiskChip, StatusChip, ago } from '../components/ui'

export default function Worker() {
  const [tasks, setTasks] = useState(null)
  const [err, setErr] = useState('')

  const load = useCallback(() => api('/api/reports').then(setTasks).catch((e) => setErr(e.message)), [])
  useEffect(() => {
    load()
    const t = setInterval(load, 15000)
    return () => clearInterval(t)
  }, [load])

  if (tasks === null) return <p className="muted">Loading…</p>
  const todo = tasks.filter((t) => t.status === 'assigned')
  const done = tasks.filter((t) => t.status === 'cleaned' || t.status === 'closed')

  return (
    <section className="card">
      <h1>My tasks</h1>
      <p className="err">{err}</p>
      {todo.length === 0 ? <Empty title="No tasks right now" text="When the officer assigns you a spot, it shows up here." /> :
        todo.map((t) => <Task key={t.id} t={t} onDone={load} />)}
      {done.length > 0 && (
        <>
          <h2>Done</h2>
          <div className="list">{done.map((t) => (
            <div key={t.id} className="item static">
              <img className="th" src={t.after_photo_url || t.photo_url} alt="" />
              <span className="mid"><span className="t">Ward {t.ward_id} · {t.ward_name}</span><span className="s">Cleaned {ago(t.cleaned_at)}</span></span>
              <span className="r"><StatusChip status={t.status} /></span>
            </div>
          ))}</div>
        </>
      )}
    </section>
  )
}

function Task({ t, onDone }) {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const submit = async () => {
    const form = new FormData()
    form.append('photo', file)
    setBusy(true)
    try {
      await api(`/api/reports/${t.id}/clean`, { method: 'POST', form })
      onDone()
    } catch (e) {
      setErr(e.message)
      setBusy(false)
    }
  }

  return (
    <article className="task">
      <div className="side">
        <Photo src={t.photo_url} caption="Reported" />
        <MapView reports={[t]} focus={t} height={180} />
        <a className="btn small" href={`https://www.google.com/maps/dir/?api=1&destination=${t.lat},${t.lon}`} target="_blank" rel="noreferrer">Directions</a>
      </div>
      <div className="mainc">
        <div className="cardhead"><h3>Ward {t.ward_id} · {t.ward_name}</h3><RiskChip risk={t.risk} /></div>
        {t.note && <p className="note">“{t.note}”</p>}
        <p className="muted small">{t.detection.summary} · assigned {ago(t.assigned_at)}</p>
        <ol className="how small">
          <li>Go to the pin and check the spot.</li>
          <li>Empty the water, remove the container or treat it.</li>
          <li>Take an after photo and mark it cleaned.</li>
        </ol>
        <label className="afterdrop" htmlFor={`after-${t.id}`}>
          {preview ? <><img src={preview} alt="After" /> After photo added · tap to change</> : 'Add after photo'}
        </label>
        <input id={`after-${t.id}`} className="sr" type="file" accept="image/*" capture="environment"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) { setFile(f); setPreview(URL.createObjectURL(f)) } }} />
        <div><button className="btn primary" disabled={!file || busy} onClick={submit}>{busy ? 'Uploading…' : 'Mark as cleaned'}</button></div>
        <p className="err">{err}</p>
      </div>
    </article>
  )
}
