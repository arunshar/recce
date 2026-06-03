import type { Candidate } from '../types'
import { scoreColor } from '../util'

interface Props {
  c: Candidate
  selected: boolean
  onToggle: (id: string) => void
  conceptUrl?: string
}

export default function CandidateCard({ c, selected, onToggle, conceptUrl }: Props) {
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
        <div className="grid h-20 w-28 flex-none grid-rows-2 gap-1">
          {c.street_view_url && (
            <img
              src={c.street_view_url}
              alt={c.name}
              className="h-full w-full rounded bg-slate-800 object-cover"
            />
          )}
          {conceptUrl ? (
            <img
              src={conceptUrl}
              alt={`${c.name} concept reference`}
              className="h-full w-full rounded bg-slate-800 object-cover"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center rounded bg-slate-800 text-[10px] text-slate-500">
              concept
            </div>
          )}
        </div>
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
          <div className="mt-1 flex flex-wrap gap-1">
            {c.source && (
              <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400">
                {c.source.replaceAll('_', ' ')}
              </span>
            )}
            {c.permit_required && (
              <span className="rounded bg-fuchsia-500/15 px-1.5 py-0.5 text-[10px] text-fuchsia-300">
                permit
              </span>
            )}
          </div>
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
