import type { Candidate } from '../types'
import { scoreColor } from '../util'

interface Props {
  c: Candidate
  selected: boolean
  onToggle: (id: string) => void
}

export default function CandidateCard({ c, selected, onToggle }: Props) {
  return (
    <button
      type="button"
      onClick={() => onToggle(c.id)}
      className={`w-full rounded-lg border p-2 text-left transition ${
        selected
          ? 'border-sky-400 bg-slate-800'
          : 'border-slate-700 bg-slate-900 hover:border-slate-500'
      }`}
    >
      <div className="flex gap-3">
        {c.street_view_url && (
          <img
            src={c.street_view_url}
            alt={c.name}
            className="h-16 w-24 flex-none rounded bg-slate-800 object-cover"
          />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span
              className="rounded px-1.5 py-0.5 text-xs font-bold text-slate-900"
              style={{ backgroundColor: scoreColor(c.match_score) }}
            >
              {c.match_score}
            </span>
            <span className="truncate font-medium text-slate-100">{c.name}</span>
            {selected && <span className="ml-auto text-xs text-sky-400">shortlisted</span>}
          </div>
          <div className="truncate text-xs text-slate-400">{c.address}</div>
          <div className="mt-1 line-clamp-2 text-xs text-slate-300">{c.rationale}</div>
          {c.flags.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {c.flags.map((f, i) => (
                <span
                  key={i}
                  className="rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] text-amber-300"
                >
                  {f}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </button>
  )
}
