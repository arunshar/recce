import type { SceneBrief, Candidate, RouteResult, Packet, Health, LatLng } from './types'

async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${url} responded ${r.status}`)
  return r.json() as Promise<T>
}

async function postJSON<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(`${url} responded ${r.status}`)
  return r.json() as Promise<T>
}

export const getHealth = () => getJSON<Health>('/api/health')

export const getSampleScene = () => getJSON<{ scene_text: string }>('/api/demo/scene')

export const analyzeScene = (scene_text: string, base_city: string) =>
  postJSON<{ base_city: string; demo_mode: boolean; briefs: SceneBrief[] }>('/api/analyze', {
    scene_text,
    base_city,
  })

export const findCandidates = (briefs: SceneBrief[], base_city: string) =>
  postJSON<{ base_city: string; center: LatLng; demo_mode: boolean; candidates: Candidate[] }>(
    '/api/candidates',
    { briefs, base_city },
  )

export const planRoute = (candidates: Candidate[], base_city: string, shoot_date?: string) =>
  postJSON<RouteResult>('/api/route', { candidates, base_city, shoot_date })

export const generatePacket = (
  candidates: Candidate[],
  briefs: SceneBrief[],
  base_city: string,
  shoot_date?: string,
  production_title?: string,
) =>
  postJSON<Packet>('/api/packet', { candidates, briefs, base_city, shoot_date, production_title })

export async function generateMoodboard(brief: SceneBrief): Promise<string> {
  const r = await fetch('/api/moodboard', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(brief),
  })
  if (!r.ok) throw new Error(`/api/moodboard responded ${r.status}`)
  const blob = await r.blob()
  return URL.createObjectURL(blob)
}
