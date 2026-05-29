import { useEffect, useState, type ReactNode } from 'react'
import MapView from './components/MapView'
import CandidateCard from './components/CandidateCard'
import * as api from './api'
import type { SceneBrief, Candidate, LatLng, RouteResult, Packet, Health } from './types'

const DEFAULT_CENTER: LatLng = { lat: 34.0522, lng: -118.2437 }

function Chip({ children }: { children: ReactNode }) {
  return (
    <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-slate-300">
      {children}
    </span>
  )
}

function ModeBadge({ health }: { health: Health }) {
  const live = health.has_gemini && health.has_maps
  const partial = !live && (health.has_gemini || health.has_maps)
  const label = live ? 'Live: Gemini + Maps' : partial ? 'Partial keys' : 'Demo mode'
  const color = live
    ? 'bg-emerald-500/15 text-emerald-300'
    : partial
      ? 'bg-sky-500/15 text-sky-300'
      : 'bg-amber-500/15 text-amber-300'
  return <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${color}`}>{label}</span>
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [sceneText, setSceneText] = useState('')
  const [baseCity, setBaseCity] = useState('Los Angeles, CA')
  const [briefs, setBriefs] = useState<SceneBrief[]>([])
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [center, setCenter] = useState<LatLng>(DEFAULT_CENTER)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [route, setRoute] = useState<RouteResult | null>(null)
  const [packet, setPacket] = useState<Packet | null>(null)
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [moodImages, setMoodImages] = useState<Record<string, string>>({})
  const [moodBusy, setMoodBusy] = useState<Set<string>>(new Set())

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => {})
  }, [])

  const fail = (e: unknown, prefix = '') =>
    setError(prefix + (e instanceof Error ? e.message : String(e)))

  const loadSample = async () => {
    try {
      const { scene_text } = await api.getSampleScene()
      setSceneText(scene_text)
    } catch (e) {
      fail(e)
    }
  }

  const runScout = async () => {
    setError('')
    setRoute(null)
    setPacket(null)
    try {
      setBusy('Reading the scene with Gemini...')
      const a = await api.analyzeScene(sceneText, baseCity)
      setBriefs(a.briefs)
      setBusy('Finding and scoring locations...')
      const res = await api.findCandidates(a.briefs, baseCity)
      setCandidates(res.candidates)
      setCenter(res.center)
      // Pre-shortlist the top candidate per scene.
      const byScene = new Map<string, Candidate>()
      for (const c of res.candidates) {
        const best = byScene.get(c.scene_id)
        if (!best || c.match_score > best.match_score) byScene.set(c.scene_id, c)
      }
      setSelected(new Set([...byScene.values()].map((c) => c.id)))
    } catch (e) {
      fail(e)
    } finally {
      setBusy('')
    }
  }

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  const selectedCandidates = candidates.filter((c) => selected.has(c.id))

  const planDay = async () => {
    setError('')
    try {
      setBusy('Optimizing scout-day route...')
      setRoute(await api.planRoute(selectedCandidates, baseCity))
    } catch (e) {
      fail(e, 'Could not plan the route: ')
    } finally {
      setBusy('')
    }
  }

  const makePacket = async () => {
    setError('')
    try {
      setBusy('Generating the shoot-day packet...')
      setPacket(await api.generatePacket(selectedCandidates, briefs, baseCity))
    } catch (e) {
      fail(e, 'Could not generate the packet: ')
    } finally {
      setBusy('')
    }
  }

  const makeMood = async (brief: SceneBrief) => {
    setError('')
    setMoodBusy((prev) => new Set(prev).add(brief.scene_id))
    try {
      const url = await api.generateMoodboard(brief)
      setMoodImages((prev) => ({ ...prev, [brief.scene_id]: url }))
    } catch (e) {
      fail(e, 'Mood board failed: ')
    } finally {
      setMoodBusy((prev) => {
        const next = new Set(prev)
        next.delete(brief.scene_id)
        return next
      })
    }
  }

  return (
    <div className="flex h-full flex-col bg-slate-950 text-slate-100">
      <header className="flex h-14 flex-none items-center justify-between border-b border-slate-800 px-4">
        <div className="flex items-baseline gap-2">
          <span className="text-xl font-semibold tracking-tight">Recce</span>
          <span className="hidden text-xs text-slate-400 sm:inline">
            AI location scouting, from script to shoot day
          </span>
        </div>
        {health && <ModeBadge health={health} />}
      </header>

      <div className="flex min-h-0 flex-1">
        <aside className="flex w-[460px] flex-none flex-col border-r border-slate-800">
          {/* Scene input */}
          <div className="flex-none space-y-2 border-b border-slate-800 p-3">
            <textarea
              value={sceneText}
              onChange={(e) => setSceneText(e.target.value)}
              placeholder="Paste a screenplay scene, or load the sample..."
              className="h-28 w-full resize-none rounded-md border border-slate-700 bg-slate-900 p-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-sky-500 focus:outline-none"
            />
            <div className="flex gap-2">
              <input
                value={baseCity}
                onChange={(e) => setBaseCity(e.target.value)}
                placeholder="Production base city"
                className="min-w-0 flex-1 rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-100 focus:border-sky-500 focus:outline-none"
              />
              <button
                type="button"
                onClick={loadSample}
                className="flex-none rounded-md border border-slate-700 px-2.5 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
              >
                Sample
              </button>
            </div>
            <button
              type="button"
              onClick={runScout}
              disabled={!sceneText.trim() || !!busy}
              className="w-full rounded-md bg-sky-500 py-2 text-sm font-semibold text-slate-950 hover:bg-sky-400 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-400"
            >
              Find locations
            </button>
          </div>

          {/* Results */}
          <div className="min-h-0 flex-1 overflow-y-auto px-3 py-2">
            {briefs.length === 0 && (
              <p className="mt-10 text-center text-sm text-slate-500">
                Your scenes and scored locations will appear here.
              </p>
            )}
            {briefs.map((b) => (
              <div key={b.scene_id} className="mb-4">
                <div className="text-sm font-semibold text-slate-200">{b.slugline || b.scene_id}</div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {b.int_ext && <Chip>{b.int_ext}</Chip>}
                  {b.time_of_day && <Chip>{b.time_of_day}</Chip>}
                  {b.mood.slice(0, 3).map((m, i) => (
                    <Chip key={i}>{m}</Chip>
                  ))}
                </div>
                <button
                  type="button"
                  onClick={() => makeMood(b)}
                  disabled={moodBusy.has(b.scene_id)}
                  className="mt-1.5 rounded border border-slate-700 px-2 py-0.5 text-[11px] text-slate-300 hover:bg-slate-800 disabled:opacity-50"
                >
                  {moodBusy.has(b.scene_id)
                    ? 'Generating mood board...'
                    : moodImages[b.scene_id]
                      ? 'Regenerate mood board'
                      : 'Mood board'}
                </button>
                {moodImages[b.scene_id] && (
                  <img
                    src={moodImages[b.scene_id]}
                    alt={`${b.slugline} mood board`}
                    className="mt-2 w-full rounded-lg border border-slate-800"
                  />
                )}
                <div className="mt-2 space-y-2">
                  {candidates
                    .filter((c) => c.scene_id === b.scene_id)
                    .map((c) => (
                      <CandidateCard
                        key={c.id}
                        c={c}
                        selected={selected.has(c.id)}
                        onToggle={toggle}
                      />
                    ))}
                </div>
              </div>
            ))}

            {route && (
              <div className="mb-4 rounded-lg border border-sky-900 bg-sky-950/40 p-3">
                <div className="mb-2 text-sm font-semibold text-sky-200">Scout-day route</div>
                <ol className="space-y-1.5">
                  {route.stops.map((s) => (
                    <li key={s.candidate_id} className="flex items-start gap-2 text-xs">
                      <span className="flex h-5 w-5 flex-none items-center justify-center rounded-full bg-sky-500 font-bold text-slate-950">
                        {s.order}
                      </span>
                      <div>
                        <div className="text-slate-100">{s.name}</div>
                        <div className="text-slate-400">
                          +{s.drive_minutes_from_prev.toFixed(0)} min
                          {s.arrive_local && ` · arrive ~${s.arrive_local}`}
                          {s.window_note && ` · ${s.window_note}`}
                        </div>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>

          {/* Actions */}
          {candidates.length > 0 && (
            <div className="flex-none border-t border-slate-800 p-3">
              <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
                <span>
                  {selected.size} location{selected.size === 1 ? '' : 's'} shortlisted
                </span>
                {route && (
                  <span>
                    {route.total_drive_minutes.toFixed(0)} min &middot;{' '}
                    {route.total_distance_km.toFixed(0)} km
                  </span>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={planDay}
                  disabled={selected.size === 0 || !!busy}
                  className="flex-1 rounded-md border border-slate-700 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800 disabled:opacity-50"
                >
                  Plan scout day
                </button>
                <button
                  type="button"
                  onClick={makePacket}
                  disabled={selected.size === 0 || !!busy}
                  className="flex-1 rounded-md bg-emerald-500 py-2 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-50"
                >
                  Shoot-day packet
                </button>
              </div>
            </div>
          )}
        </aside>

        <main className="relative min-w-0 flex-1">
          <MapView
            center={center}
            candidates={candidates}
            selectedIds={selected}
            onToggle={toggle}
            route={route}
          />
          {busy && (
            <div className="pointer-events-none absolute left-1/2 top-4 z-[1000] -translate-x-1/2 rounded-full bg-slate-900/90 px-4 py-2 text-sm text-slate-100 shadow-lg ring-1 ring-slate-700">
              {busy}
            </div>
          )}
          {error && (
            <div className="absolute left-1/2 top-4 z-[1000] -translate-x-1/2 rounded-md bg-red-950/90 px-4 py-2 text-sm text-red-200 shadow-lg ring-1 ring-red-800">
              {error}
              <button className="ml-3 text-red-400 hover:text-red-200" onClick={() => setError('')}>
                dismiss
              </button>
            </div>
          )}
        </main>
      </div>

      {packet && <PacketPanel packet={packet} onClose={() => setPacket(null)} />}
    </div>
  )
}

function PacketPanel({ packet, onClose }: { packet: Packet; onClose: () => void }) {
  const copy = () => navigator.clipboard?.writeText(packetToText(packet)).catch(() => {})
  return (
    <div className="fixed inset-0 z-[2000] flex justify-end bg-black/50" onClick={onClose}>
      <div
        className="flex h-full w-[520px] max-w-full flex-col bg-slate-900 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex flex-none items-center justify-between border-b border-slate-800 p-4">
          <div>
            <div className="text-lg font-semibold">Shoot-day packet</div>
            <div className="text-xs text-slate-400">
              {packet.base_city}
              {packet.shoot_date && ` · ${packet.shoot_date}`}
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={copy}
              className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800"
            >
              Copy
            </button>
            <button
              onClick={onClose}
              className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-800"
            >
              Close
            </button>
          </div>
        </div>
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
          {packet.locations.map((loc, i) => (
            <div key={i} className="rounded-lg border border-slate-800 bg-slate-950 p-3">
              <div className="font-medium text-slate-100">{loc.name}</div>
              <div className="text-xs text-slate-400">{loc.address}</div>
              <dl className="mt-2 space-y-1 text-xs text-slate-300">
                {(loc.golden_hour_am || loc.golden_hour_pm) && (
                  <div>
                    <span className="text-slate-500">Golden hour: </span>
                    {loc.golden_hour_am && `AM ${loc.golden_hour_am}`}
                    {loc.golden_hour_am && loc.golden_hour_pm && ' · '}
                    {loc.golden_hour_pm && `PM ${loc.golden_hour_pm}`}
                  </div>
                )}
                {loc.sun_note && <div className="text-slate-400">{loc.sun_note}</div>}
                {loc.parking.length > 0 && (
                  <div>
                    <span className="text-slate-500">Parking: </span>
                    {loc.parking.join('; ')}
                  </div>
                )}
                {loc.nearest_hospital && (
                  <div>
                    <span className="text-slate-500">Nearest hospital: </span>
                    {loc.nearest_hospital}
                  </div>
                )}
                {loc.power_note && (
                  <div>
                    <span className="text-slate-500">Power: </span>
                    {loc.power_note}
                  </div>
                )}
                {loc.permit_note && (
                  <div>
                    <span className="text-slate-500">Permits: </span>
                    {loc.permit_note}
                  </div>
                )}
                {loc.shotlist.length > 0 && (
                  <div>
                    <span className="text-slate-500">Shotlist: </span>
                    <ul className="ml-4 list-disc">
                      {loc.shotlist.map((s, j) => (
                        <li key={j}>{s}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </dl>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function packetToText(p: Packet): string {
  const lines: string[] = [
    `SHOOT-DAY PACKET — ${p.production_title}`,
    `Base: ${p.base_city}${p.shoot_date ? `   Date: ${p.shoot_date}` : ''}`,
    '',
  ]
  p.locations.forEach((loc, i) => {
    lines.push(`${i + 1}. ${loc.name} — ${loc.address}`)
    if (loc.golden_hour_am || loc.golden_hour_pm)
      lines.push(`   Golden hour: AM ${loc.golden_hour_am}  PM ${loc.golden_hour_pm}`)
    if (loc.sun_note) lines.push(`   ${loc.sun_note}`)
    if (loc.parking.length) lines.push(`   Parking: ${loc.parking.join('; ')}`)
    if (loc.nearest_hospital) lines.push(`   Nearest hospital: ${loc.nearest_hospital}`)
    if (loc.power_note) lines.push(`   Power: ${loc.power_note}`)
    if (loc.permit_note) lines.push(`   Permits: ${loc.permit_note}`)
    loc.shotlist.forEach((s) => lines.push(`   - ${s}`))
    lines.push('')
  })
  if (p.notes) lines.push(p.notes)
  return lines.join('\n')
}
