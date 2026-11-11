import { useEffect, useState } from 'react'
import { api } from '../api'
import MapView from '../components/MapView'
import { DetectionCard, Photo, Progress, RiskCard } from '../components/ui'

export default function Report() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [point, setPoint] = useState(null)
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState('')
  const [err, setErr] = useState('')
  const [result, setResult] = useState(null)
  const [mapReports, setMapReports] = useState([])
  const [wards, setWards] = useState([])

  const loadMap = () => api('/api/reports/map').then(setMapReports).catch(() => {})
  useEffect(() => {
    loadMap()
    api('/api/wards').then(setWards).catch(() => {})
  }, [])

  const pickFile = (e) => {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setResult(null)
    setErr('')
  }

  const useGps = () => {
    if (!navigator.geolocation) return setErr('This browser cannot read your location. Tap the map instead.')
    setBusy('Finding your location…')
    navigator.geolocation.getCurrentPosition(
      (p) => { setPoint({ lat: p.coords.latitude, lon: p.coords.longitude }); setBusy(''); setErr('') },
      () => { setBusy(''); setErr('Location permission was refused. Tap the map to mark the place.') },
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  const submit = async () => {
    if (!file) return setErr('Add a photo first.')
    if (!point) return setErr('Mark the place: use your location or tap the map.')
    setErr('')
    setBusy('AI is checking the photo…')
    const form = new FormData()
    form.append('photo', file)
    form.append('lat', point.lat)
    form.append('lon', point.lon)
    form.append('note', note)
    try {
      const res = await api('/api/reports', { method: 'POST', form })
      setResult({ ...res, preview })
      setFile(null); setPreview(null); setPoint(null); setNote('')
      loadMap()
    } catch (e) {
      setErr(e.message)
    } finally {
      setBusy('')
    }
  }

  return (
    <div className="grid2">
      <section className="card">
        <div>
          <h1>Report a breeding spot</h1>
          <p className="muted">Seen stagnant water, an open tank or an old tyre full of rain? Send a photo and a health worker will check it.</p>
        </div>

        <div className="step"><span className="num">1</span><div className="stepbody">
          <h3>Add a photo</h3>
          <label className="drop" htmlFor="photo">
            {preview ? <><img src={preview} alt="Your photo" /><small>Tap to change</small></> : <><span>Take or choose a photo</span><small>Opens the camera on a phone</small></>}
          </label>
          <input id="photo" className="sr" type="file" accept="image/*" capture="environment" onChange={pickFile} />
        </div></div>

        <div className="step"><span className="num">2</span><div className="stepbody">
          <h3>Mark the place</h3>
          <div className="row">
            <button className="btn small" onClick={useGps} type="button">Use my location</button>
            <span className="muted small">or tap the map</span>
          </div>
          <MapView reports={mapReports} wards={wards} picked={point} onPick={setPoint} focus={point} height={300} />
          <p className="muted small">{point ? `Marked at ${point.lat.toFixed(5)}, ${point.lon.toFixed(5)}` : 'No place marked yet'}</p>
        </div></div>

        <div className="step"><span className="num">3</span><div className="stepbody">
          <h3>Add a note <span className="opt">optional</span></h3>
          <textarea id="note" rows={2} maxLength={300} value={note} onChange={(e) => setNote(e.target.value)} placeholder="e.g. Behind the bus stand, next to the tea shop" />
        </div></div>

        <button className="btn primary" onClick={submit} disabled={!!busy}>{busy || 'Send report'}</button>
        <p className="err" role="alert">{err}</p>
      </section>

      <section className="card" aria-live="polite">
        {result ? (
          <>
            <div className="cardhead"><h2>{result.duplicate ? 'Already reported' : 'Report sent'}</h2></div>
            <div className={`banner ${result.duplicate ? 'warn' : ''}`}>{result.message}</div>
            <div className="photos"><Photo src={result.preview} caption="Your photo" /></div>
            <DetectionCard d={result.report.detection} />
            <RiskCard risk={result.report.risk} />
            <Progress r={result.report} />
            <button className="btn" onClick={() => setResult(null)}>Report another spot</button>
          </>
        ) : (
          <>
            <h2>How it works</h2>
            <ol className="how">
              <li>You send a photo and mark the place.</li>
              <li>AI checks the photo for stagnant water and containers.</li>
              <li>The risk score uses the AI result, recent rain and dengue cases nearby.</li>
              <li>The officer sends a field worker, who cleans it and uploads proof.</li>
            </ol>
            <p className="muted small">Pins on the map are open reports. Red is high risk.</p>
          </>
        )}
      </section>
    </div>
  )
}
