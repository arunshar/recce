import { useEffect, useMemo, useState, type ReactNode } from 'react'
import MapView from './components/MapView'
import CandidateCard from './components/CandidateCard'
import * as api from './api'
import type { SceneBrief, ScriptScene, Candidate, LatLng, RouteResult, Packet, Health } from './types'

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
  const [scriptScenes, setScriptScenes] = useState<ScriptScene[]>([])
  const [enabledScenes, setEnabledScenes] = useState<Set<string>>(new Set())
  const [baseCity, setBaseCity] = useState('Los Angeles, CA')
  const [shootDate, setShootDate] = useState('')
  const [briefs, setBriefs] = useState<SceneBrief[]>([])
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [center, setCenter] = useState<LatLng>(DEFAULT_CENTER)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [permitFilter, setPermitFilter] = useState<'all' | 'required' | 'not-required'>('all')
  const [moodFilter, setMoodFilter] = useState('all')
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
      await previewSegments(scene_text)
    } catch (e) {
      fail(e)
    }
  }

  const previewSegments = async (text: string) => {
    const res = await api.segmentScript(text)
    setScriptScenes(res.scenes)
    setEnabledScenes(new Set(res.scenes.map((s) => s.scene_id)))
  }

  const loadScriptFile = async (file: File | undefined) => {
    if (!file) return
    try {
      const text = await file.text()
      setSceneText(text)
      await previewSegments(text)
    } catch (e) {
      fail(e, 'Could not read script: ')
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
      const sceneIds =
        enabledScenes.size > 0 ? enabledScenes : new Set(a.briefs.map((brief) => brief.scene_id))
      const briefsToSearch = a.briefs.filter((brief) => sceneIds.has(brief.scene_id))
      if (briefsToSearch.length === 0) {
        throw new Error('Select at least one scene before searching.')
      }
      setBusy('Finding and scoring locations...')
      const res = await api.findCandidates(briefsToSearch, baseCity)
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

  const moodOptions = useMemo(() => {
    const moods = new Set<string>()
    briefs.forEach((brief) => brief.mood.forEach((mood) => moods.add(mood)))
    return [...moods].sort()
  }, [briefs])

  const sceneIsActive = (sceneId: string) => enabledScenes.size === 0 || enabledScenes.has(sceneId)

  const briefMatchesFilters = (brief: SceneBrief) =>
    sceneIsActive(brief.scene_id) && (moodFilter === 'all' || brief.mood.includes(moodFilter))

  const candidateMatchesFilters = (candidate: Candidate) => {
    if (!sceneIsActive(candidate.scene_id)) return false
    if (permitFilter === 'required' && !candidate.permit_required) return false
    if (permitFilter === 'not-required' && candidate.permit_required) return false
    if (moodFilter !== 'all') {
      const brief = briefs.find((b) => b.scene_id === candidate.scene_id)
      if (!brief?.mood.includes(moodFilter)) return false
    }
    return true
  }

  const visibleBriefs = briefs.filter(briefMatchesFilters)
  const selectedCandidates = candidates.filter((c) => selected.has(c.id) && sceneIsActive(c.scene_id))

  const planDay = async () => {
    setError('')
    try {
      setBusy('Optimizing scout-day route...')
      setRoute(await api.planRoute(selectedCandidates, baseCity, shootDate || undefined))
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
      setPacket(await api.generatePacket(selectedCandidates, briefs, baseCity, shootDate || undefined))
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
              onChange={(e) => {
                setSceneText(e.target.value)
                setScriptScenes([])
                setEnabledScenes(new Set())
              }}
              placeholder="Paste a screenplay scene or full script, upload a file, or load the sample..."
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
              <label className="flex-none cursor-pointer rounded-md border border-slate-700 px-2.5 py-1.5 text-sm text-slate-300 hover:bg-slate-800">
                Upload
                <input
                  type="file"
                  accept=".txt,.fountain,.fdx"
                  className="hidden"
                  onChange={(e) => loadScriptFile(e.target.files?.[0])}
                />
              </label>
            </div>
            {scriptScenes.length > 0 && (
              <div className="max-h-28 space-y-1 overflow-y-auto rounded-md border border-slate-800 bg-slate-900 p-2">
                {scriptScenes.map((scene) => (
                  <label key={scene.scene_id} className="flex items-start gap-2 text-xs text-slate-300">
                    <input
                      type="checkbox"
                      checked={enabledScenes.has(scene.scene_id)}
                      onChange={() =>
                        setEnabledScenes((prev) => {
                          const next = new Set(prev)
                          if (next.has(scene.scene_id)) next.delete(scene.scene_id)
                          else next.add(scene.scene_id)
                          return next
                        })
                      }
                      className="mt-0.5"
                    />
                    <span className="min-w-0">
                      <span className="font-medium text-slate-200">{scene.scene_id}</span>{' '}
                      <span className="break-words">{scene.slugline}</span>
                    </span>
                  </label>
                ))}
              </div>
            )}
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
            {briefs.length > 0 && (
              <div className="sticky top-0 z-10 mb-3 grid grid-cols-2 gap-2 border-b border-slate-900 bg-slate-950 pb-2">
                <select
                  value={moodFilter}
                  onChange={(e) => setMoodFilter(e.target.value)}
                  className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-200 focus:border-sky-500 focus:outline-none"
                >
                  <option value="all">All moods</option>
                  {moodOptions.map((mood) => (
                    <option key={mood} value={mood}>
                      {mood}
                    </option>
                  ))}
                </select>
                <select
                  value={permitFilter}
                  onChange={(e) =>
                    setPermitFilter(e.target.value as 'all' | 'required' | 'not-required')
                  }
                  className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-200 focus:border-sky-500 focus:outline-none"
                >
                  <option value="all">All permits</option>
                  <option value="required">Permit required</option>
                  <option value="not-required">No permit flag</option>
                </select>
              </div>
            )}
            {briefs.length === 0 && (
              <p className="mt-10 text-center text-sm text-slate-500">
                Your scenes and scored locations will appear here.
              </p>
            )}
            {visibleBriefs.map((b) => (
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
                    .filter((c) => c.scene_id === b.scene_id && candidateMatchesFilters(c))
                    .map((c) => (
                      <CandidateCard
                        key={c.id}
                        c={c}
                        selected={selected.has(c.id)}
                        onToggle={toggle}
                        conceptUrl={moodImages[c.scene_id]}
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
                  {selectedCandidates.length} location
                  {selectedCandidates.length === 1 ? '' : 's'} shortlisted
                </span>
                {route && (
                  <span>
                    {route.total_drive_minutes.toFixed(0)} min &middot;{' '}
                    {route.total_distance_km.toFixed(0)} km &middot;{' '}
                    {route.route_method === 'osrm_trip' ? 'OSRM' : '2-opt'}
                  </span>
                )}
              </div>
              <input
                type="date"
                value={shootDate}
                onChange={(e) => setShootDate(e.target.value)}
                className="mb-2 w-full rounded-md border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm text-slate-200 focus:border-sky-500 focus:outline-none"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={planDay}
                  disabled={selectedCandidates.length === 0 || !!busy}
                  className="flex-1 rounded-md border border-slate-700 py-2 text-sm font-medium text-slate-200 hover:bg-slate-800 disabled:opacity-50"
                >
                  Plan scout day
                </button>
                <button
                  type="button"
                  onClick={makePacket}
                  disabled={selectedCandidates.length === 0 || !!busy}
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
          {packet.schedule.length > 0 && (
            <div className="rounded-lg border border-sky-900 bg-sky-950/30 p-3">
              <div className="mb-2 text-sm font-semibold text-sky-200">Shoot schedule</div>
              <div className="space-y-3">
                {packet.schedule.map((day) => (
                  <div key={day.day}>
                    <div className="mb-1 text-xs font-medium uppercase text-slate-400">
                      Day {day.day} · {day.date}
                    </div>
                    <div className="grid gap-1">
                      {day.stops.map((stop) => (
                        <div
                          key={`${day.day}-${stop.order}`}
                          className="grid grid-cols-[4.5rem_1fr] gap-2 rounded border border-slate-800 bg-slate-950 px-2 py-1.5 text-xs"
                        >
                          <div className="text-slate-400">{stop.start_local}</div>
                          <div className="min-w-0">
                            <div className="truncate text-slate-100">{stop.location_name}</div>
                            <div className="truncate text-slate-500">
                              {stop.golden_window && `golden ${stop.golden_window}`}
                              {stop.golden_window && stop.weather_summary && ' · '}
                              {stop.weather_summary}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {packet.locations.map((loc, i) => (
            <div key={i} className="rounded-lg border border-slate-800 bg-slate-950 p-3">
              <div className="flex gap-3">
                {loc.concept_image_url && (
                  <img
                    src={loc.concept_image_url}
                    alt={`${loc.name} concept frame`}
                    className="h-24 w-36 flex-none rounded bg-slate-800 object-cover"
                  />
                )}
                <div className="min-w-0 flex-1">
                  <div className="font-medium text-slate-100">{loc.name}</div>
                  <div className="text-xs text-slate-400">{loc.address}</div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {loc.scene_id && (
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">
                        {loc.scene_id}
                      </span>
                    )}
                    {loc.permit_required && (
                      <span className="rounded bg-fuchsia-500/15 px-1.5 py-0.5 text-[10px] text-fuchsia-300">
                        permit review
                      </span>
                    )}
                    {loc.weather?.source && (
                      <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] text-emerald-300">
                        weather {loc.weather.source}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <dl className="mt-2 space-y-1 text-xs text-slate-300">
                {(loc.golden_hour_am || loc.golden_hour_pm) && (
                  <div>
                    <span className="text-slate-500">Golden hour: </span>
                    {loc.golden_hour_am && `AM ${loc.golden_hour_am}`}
                    {loc.golden_hour_am && loc.golden_hour_pm && ' · '}
                    {loc.golden_hour_pm && `PM ${loc.golden_hour_pm}`}
                  </div>
                )}
                {(loc.sunrise || loc.sunset) && (
                  <div>
                    <span className="text-slate-500">Sun: </span>
                    {loc.sunrise && `sunrise ${loc.sunrise}`}
                    {loc.sunrise && loc.sunset && ' · '}
                    {loc.sunset && `sunset ${loc.sunset}`}
                  </div>
                )}
                {loc.sun_note && <div className="text-slate-400">{loc.sun_note}</div>}
                {loc.weather?.summary && (
                  <div>
                    <span className="text-slate-500">Weather: </span>
                    {loc.weather.summary}
                  </div>
                )}
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
                {loc.permit_restrictions.length > 0 && (
                  <div>
                    <span className="text-slate-500">Restrictions: </span>
                    {loc.permit_restrictions.join('; ')}
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
  if (p.schedule.length) {
    lines.push('SCHEDULE')
    p.schedule.forEach((day) => {
      lines.push(`Day ${day.day} — ${day.date}`)
      day.stops.forEach((stop) => {
        lines.push(
          `   ${stop.start_local}  ${stop.location_name}` +
            `${stop.golden_window ? `  golden ${stop.golden_window}` : ''}` +
            `${stop.weather_summary ? `  weather ${stop.weather_summary}` : ''}`,
        )
      })
    })
    lines.push('')
  }
  p.locations.forEach((loc, i) => {
    lines.push(`${i + 1}. ${loc.name} — ${loc.address}`)
    if (loc.golden_hour_am || loc.golden_hour_pm)
      lines.push(`   Golden hour: AM ${loc.golden_hour_am}  PM ${loc.golden_hour_pm}`)
    if (loc.sun_note) lines.push(`   ${loc.sun_note}`)
    if (loc.weather?.summary) lines.push(`   Weather: ${loc.weather.summary}`)
    if (loc.parking.length) lines.push(`   Parking: ${loc.parking.join('; ')}`)
    if (loc.nearest_hospital) lines.push(`   Nearest hospital: ${loc.nearest_hospital}`)
    if (loc.power_note) lines.push(`   Power: ${loc.power_note}`)
    if (loc.permit_note) lines.push(`   Permits: ${loc.permit_note}`)
    if (loc.permit_restrictions.length)
      lines.push(`   Restrictions: ${loc.permit_restrictions.join('; ')}`)
    loc.shotlist.forEach((s) => lines.push(`   - ${s}`))
    lines.push('')
  })
  if (p.notes) lines.push(p.notes)
  return lines.join('\n')
}
