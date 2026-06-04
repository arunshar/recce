import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'

const root = new URL('..', import.meta.url).pathname
const app = readFileSync(join(root, 'src/App.tsx'), 'utf8')
const types = readFileSync(join(root, 'src/types.ts'), 'utf8')
const api = readFileSync(join(root, 'src/api.ts'), 'utf8')

const requiredUiSignals = [
  'Upload',
  'Find locations',
  'All moods',
  'All permits',
  'Shoot schedule',
  'weather ',
]

const requiredTypeSignals = [
  'ScriptScene',
  'WeatherSummary',
  'ScheduleDay',
  'permit_required',
  'concept_image_url',
]

const requiredApiSignals = ['/api/script/segments', '/api/candidates', '/api/packet', '/api/moodboard']

for (const text of requiredUiSignals) assert(app.includes(text), `missing UI signal: ${text}`)
for (const text of requiredTypeSignals) assert(types.includes(text), `missing type signal: ${text}`)
for (const text of requiredApiSignals) assert(api.includes(text), `missing API signal: ${text}`)

if (existsSync(join(root, 'dist/index.html'))) {
  const html = readFileSync(join(root, 'dist/index.html'), 'utf8')
  assert(html.includes('<div id="root">'), 'dist index is missing React root')
  assert(html.includes('/assets/'), 'dist index is missing built assets')
}

console.log('Frontend smoke passed')

function assert(condition, message) {
  if (!condition) {
    console.error(`Frontend smoke failed: ${message}`)
    process.exit(1)
  }
}
