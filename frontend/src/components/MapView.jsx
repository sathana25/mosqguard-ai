import { useEffect, useState } from 'react'
import { CircleMarker, MapContainer, Rectangle, TileLayer, Tooltip, useMap, useMapEvents } from 'react-leaflet'
import { api } from '../api'

const COLORS = { High: '#c23a28', Medium: '#b97c0b', Low: '#2e8a4b' }

function ClickToPick({ onPick }) {
  useMapEvents({ click: (e) => onPick?.({ lat: e.latlng.lat, lon: e.latlng.lng }) })
  return null
}

function FlyTo({ point }) {
  const map = useMap()
  useEffect(() => {
    if (point) map.flyTo([point.lat, point.lon], Math.max(map.getZoom(), 16), { duration: 0.6 })
  }, [point?.lat, point?.lon]) // eslint-disable-line react-hooks/exhaustive-deps
  return null
}

/**
 * Map with ward outlines and report pins.
 * - reports: pins coloured by risk (closed ones grey)
 * - picked / onPick: lets a resident tap to mark a place
 * - selectedId / onSelect: officer clicks a pin to open a report
 */
export default function MapView({ reports = [], wards = [], picked, onPick, selectedId, onSelect, focus, height = 380 }) {
  const [center, setCenter] = useState(null)
  useEffect(() => {
    api('/api/config').then((c) => setCenter(c.map_center)).catch(() => setCenter([11.0168, 76.9558]))
  }, [])
  if (!center) return <div className="map" style={{ height }} />

  return (
    <div className="map" style={{ height }}>
      <MapContainer center={center} zoom={14} style={{ height: '100%' }} scrollWheelZoom={false}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {wards.map((w) => (
          <Rectangle key={w.id} bounds={w.bounds} pathOptions={{ color: '#0d6b58', weight: 1, fillOpacity: 0.04, dashArray: '4 4' }}>
            <Tooltip direction="center" opacity={0.8}>Ward {w.id} · {w.name}</Tooltip>
          </Rectangle>
        ))}
        {reports.map((r) => {
          const closed = r.status === 'closed'
          const color = closed ? '#8a9893' : COLORS[r.risk.level]
          return (
            <CircleMarker
              key={r.id}
              center={[r.lat, r.lon]}
              radius={r.id === selectedId ? 13 : 9}
              pathOptions={{ color: r.id === selectedId ? '#13231f' : '#fff', weight: r.id === selectedId ? 3 : 2, fillColor: color, fillOpacity: closed ? 0.4 : 0.95 }}
              eventHandlers={{ click: () => onSelect?.(r.id) }}
            >
              <Tooltip>Ward {r.ward_id} · {r.risk.level} risk{r.confirmations > 1 ? ` · ${r.confirmations} reports` : ''}</Tooltip>
            </CircleMarker>
          )
        })}
        {picked && (
          <CircleMarker center={[picked.lat, picked.lon]} radius={12} pathOptions={{ color: '#0d6b58', weight: 3, fillOpacity: 0.15 }} />
        )}
        {onPick && <ClickToPick onPick={onPick} />}
        <FlyTo point={focus} />
      </MapContainer>
    </div>
  )
}
