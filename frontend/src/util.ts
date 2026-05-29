// Match score -> traffic-light color used on map pins, score chips, and the route.
export function scoreColor(score: number): string {
  if (score >= 80) return '#22c55e' // green: shoot-ready
  if (score >= 60) return '#f59e0b' // amber: workable with dressing
  return '#ef4444' // red: a stretch
}
