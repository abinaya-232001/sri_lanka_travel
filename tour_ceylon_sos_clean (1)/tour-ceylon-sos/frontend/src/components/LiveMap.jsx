import { useEffect } from 'react'
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer, Tooltip, useMap } from 'react-leaflet'

function Follow({ point }) {
  const map = useMap()
  useEffect(() => { if (point) map.panTo(point, { animate: true }) }, [map, point?.[0], point?.[1]]) // eslint-disable-line react-hooks/exhaustive-deps
  return null
}

/**
 * Police map: route since SOS (red line), SOS start, current position and the station.
 * `incidents` mode shows all open cases of the station as dots.
 */
export default function LiveMap({ track = [], station, incidents, onSelect, height }) {
  const precise = track.filter((p) => p.accuracy == null || p.accuracy <= 1000)
  const points = precise.length ? precise : track
  const line = points.map((p) => [p.latitude, p.longitude])
  const current = line[line.length - 1]
  const center = current || (incidents?.[0]?.latest_location && [incidents[0].latest_location.latitude, incidents[0].latest_location.longitude])
    || (station && [station.latitude, station.longitude]) || [7.8731, 80.7718]

  return (
    <div className="map" style={height ? { height } : undefined}>
      <MapContainer center={center} zoom={incidents ? 11 : 15} style={{ height: '100%', width: '100%' }}>
        <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {line.length > 1 && <Polyline positions={line} pathOptions={{ color: '#dc2626', weight: 5, opacity: 0.85 }} />}
        {line.length > 0 && (
          <CircleMarker center={line[0]} radius={7} pathOptions={{ color: '#7f1d1d', fillColor: '#fca5a5', fillOpacity: 1 }}>
            <Tooltip>SOS started here</Tooltip>
          </CircleMarker>
        )}
        {current && (
          <CircleMarker center={current} radius={11} pathOptions={{ color: '#fff', weight: 3, fillColor: '#dc2626', fillOpacity: 1 }}>
            <Tooltip permanent direction="top">Tourist now</Tooltip>
          </CircleMarker>
        )}
        {station && (
          <CircleMarker center={[station.latitude, station.longitude]} radius={9} pathOptions={{ color: '#0a4a52', fillColor: '#14b8a6', fillOpacity: 0.9 }}>
            <Tooltip>{station.name}</Tooltip>
          </CircleMarker>
        )}
        {incidents?.map((i) => i.latest_location && (
          <CircleMarker key={i.id} center={[i.latest_location.latitude, i.latest_location.longitude]} radius={10}
            pathOptions={{ color: '#7f1d1d', fillColor: '#dc2626', fillOpacity: 0.9 }} eventHandlers={{ click: () => onSelect?.(i) }}>
            <Popup>#{i.id} {i.label}</Popup>
          </CircleMarker>
        ))}
        {current && !incidents && <Follow point={current} />}
      </MapContainer>
    </div>
  )
}
