import { useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Polyline, Tooltip, useMap } from 'react-leaflet'
import type { Candidate, LatLng, RouteResult } from '../types'
import { scoreColor } from '../util'

interface Props {
  center: LatLng
  candidates: Candidate[]
  selectedIds: Set<string>
  onToggle: (id: string) => void
  route: RouteResult | null
}

function Recenter({ center }: { center: LatLng }) {
  const map = useMap()
  useEffect(() => {
    map.setView([center.lat, center.lng])
  }, [center, map])
  return null
}

export default function MapView({ center, candidates, selectedIds, onToggle, route }: Props) {
  const line: [number, number][] = route
    ? [[route.base_lat, route.base_lng], ...route.stops.map((s) => [s.lat, s.lng] as [number, number])]
    : []

  return (
    <MapContainer center={[center.lat, center.lng]} zoom={11} className="h-full w-full bg-slate-900">
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; OpenStreetMap contributors &copy; CARTO'
      />
      <Recenter center={center} />

      <CircleMarker
        center={[center.lat, center.lng]}
        radius={8}
        pathOptions={{ color: '#ffffff', weight: 2, fillColor: '#3b82f6', fillOpacity: 1 }}
      >
        <Tooltip>Production base</Tooltip>
      </CircleMarker>

      {candidates.map((c) => {
        const selected = selectedIds.has(c.id)
        const color = scoreColor(c.match_score)
        return (
          <CircleMarker
            key={c.id}
            center={[c.lat, c.lng]}
            radius={selected ? 11 : 7}
            pathOptions={{
              color: selected ? '#ffffff' : color,
              weight: selected ? 3 : 1.5,
              fillColor: color,
              fillOpacity: 0.9,
            }}
            eventHandlers={{ click: () => onToggle(c.id) }}
          >
            <Tooltip>
              {c.name} &middot; {c.match_score}
            </Tooltip>
          </CircleMarker>
        )
      })}

      {line.length > 1 && (
        <Polyline positions={line} pathOptions={{ color: '#38bdf8', weight: 3, dashArray: '6 8' }} />
      )}
    </MapContainer>
  )
}
