export interface SceneBrief {
  scene_id: string
  slugline: string
  int_ext: string
  location_type: string
  time_of_day: string
  period: string
  mood: string[]
  key_visual_elements: string[]
  practical_needs: string[]
  search_queries: string[]
}

export interface Candidate {
  id: string
  scene_id: string
  name: string
  address: string
  lat: number
  lng: number
  place_id: string
  rating?: number | null
  types: string[]
  street_view_url?: string | null
  photo_url?: string | null
  match_score: number
  rationale: string
  flags: string[]
}

export interface LatLng {
  lat: number
  lng: number
}

export interface RouteStop {
  order: number
  candidate_id: string
  name: string
  lat: number
  lng: number
  drive_minutes_from_prev: number
  arrive_local: string
  window_note: string
}

export interface RouteResult {
  base_name: string
  base_lat: number
  base_lng: number
  stops: RouteStop[]
  total_distance_km: number
  total_drive_minutes: number
}

export interface PacketLocation {
  name: string
  address: string
  lat: number
  lng: number
  golden_hour_am: string
  golden_hour_pm: string
  sun_note: string
  parking: string[]
  nearest_hospital: string
  power_note: string
  permit_note: string
  shotlist: string[]
}

export interface Packet {
  production_title: string
  shoot_date: string
  base_city: string
  locations: PacketLocation[]
  notes: string
}

export interface Health {
  status: string
  demo_mode: boolean
  has_gemini: boolean
  has_maps: boolean
  gemini_model: string
}
