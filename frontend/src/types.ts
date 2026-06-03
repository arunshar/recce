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

export interface ScriptScene {
  scene_id: string
  slugline: string
  scene_text: string
  int_ext: string
  location_type: string
  time_of_day: string
  characters: string[]
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
  source: string
  permit_required: boolean
  permit_status: string
  permit_contact: string
  permit_restrictions: string[]
  rights_notes: string[]
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
  route_method: string
}

export interface WeatherSummary {
  summary: string
  temperature_f?: number | null
  precipitation_probability?: number | null
  wind_mph?: number | null
  source: string
}

export interface ScheduleStop {
  order: number
  scene_id: string
  location_name: string
  start_local: string
  golden_window: string
  weather_summary: string
}

export interface ScheduleDay {
  day: number
  date: string
  stops: ScheduleStop[]
}

export interface PacketLocation {
  scene_id: string
  candidate_id: string
  name: string
  address: string
  lat: number
  lng: number
  concept_image_url: string
  concept_prompt: string
  sunrise: string
  sunset: string
  golden_hour_morning_end: string
  golden_hour_evening_start: string
  golden_hour_am: string
  golden_hour_pm: string
  sun_note: string
  weather: WeatherSummary
  parking: string[]
  nearest_hospital: string
  power_note: string
  permit_note: string
  permit_required: boolean
  permit_status: string
  permit_contact: string
  permit_restrictions: string[]
  shotlist: string[]
}

export interface Packet {
  production_title: string
  shoot_date: string
  base_city: string
  locations: PacketLocation[]
  schedule: ScheduleDay[]
  notes: string
}

export interface Health {
  status: string
  demo_mode: boolean
  has_gemini: boolean
  has_maps: boolean
  has_osrm: boolean
  gemini_model: string
  weather_provider: string
}
