import { Minus, Plus } from 'lucide-react'

type Props = {
  fps: number
  onBump: (delta: number) => void
  onApply: () => void
  disabled?: boolean
}

export function FpsArc({ fps, onBump, onApply, disabled }: Props) {
  const pct = Math.min(100, (fps / 120) * 100)
  const angle = (pct / 100) * 180

  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-zimon-border/80 bg-[var(--zimon-glass)] backdrop-blur-md px-4 py-3 shadow-[0_0_24px_var(--zimon-glow)]">
      <span className="text-[10px] font-semibold uppercase tracking-wider text-zimon-muted">
        Frame rate
      </span>
      <div className="relative h-24 w-44">
        <svg viewBox="0 0 120 70" className="h-full w-full">
          <path
            d="M 12 60 A 48 48 0 0 1 108 60"
            fill="none"
            stroke="currentColor"
            className="text-zimon-border"
            strokeWidth="8"
            strokeLinecap="round"
          />
          <path
            d="M 12 60 A 48 48 0 0 1 108 60"
            fill="none"
            stroke="url(#fpsGrad)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={`${(angle / 180) * 151} 151`}
          />
          <defs>
            <linearGradient id="fpsGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="var(--zimon-accent2)" />
              <stop offset="100%" stopColor="var(--zimon-accent)" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1 pt-4">
          <span className="text-2xl font-bold tabular-nums text-zimon-fg">{fps}</span>
          <span className="text-[10px] text-zimon-muted">FPS</span>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          disabled={disabled || fps <= 1}
          onClick={() => onBump(-1)}
          className="rounded-lg border border-zimon-border p-1.5 text-zimon-fg hover:bg-zimon-panel disabled:opacity-40"
        >
          <Minus className="h-4 w-4" />
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => void onApply()}
          className="rounded-lg bg-zimon-accent px-3 py-1 text-xs font-semibold text-white hover:opacity-90 disabled:opacity-40"
        >
          Apply
        </button>
        <button
          type="button"
          disabled={disabled || fps >= 120}
          onClick={() => onBump(1)}
          className="rounded-lg border border-zimon-border p-1.5 text-zimon-fg hover:bg-zimon-panel disabled:opacity-40"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
