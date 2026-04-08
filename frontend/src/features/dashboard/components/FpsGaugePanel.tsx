import { Minus, Plus } from 'lucide-react'
import { useId } from 'react'

type Props = {
  fps: number
  onBump: (delta: number) => void
  onApply: () => void
  disabled?: boolean
  /** Narrow layout: smaller gauge, FRAME RATE title, − / + / Apply only (no duplicate readout row). */
  compact?: boolean
}

export function FpsGaugePanel({ fps, onBump, onApply, disabled, compact }: Props) {
  const gid = useId().replace(/:/g, '')
  const pct = Math.min(100, (fps / 120) * 100)
  const angle = (pct / 100) * 180
  const arcLen = 151
  const cx = 60
  const cy = 58
  const rOuter = 46
  const ticks = 13

  const tickEls = Array.from({ length: ticks }, (_, i) => {
    const t = i / (ticks - 1)
    const rad = Math.PI * (1 - t)
    const long = i % 3 === 0
    const tickLen = long ? 7 : 4
    const x1 = cx + rOuter * Math.cos(rad)
    const y1 = cy - rOuter * Math.sin(rad)
    const x2 = cx + (rOuter - tickLen) * Math.cos(rad)
    const y2 = cy - (rOuter - tickLen) * Math.sin(rad)
    return (
      <line
        key={i}
        x1={x1}
        y1={y1}
        x2={x2}
        y2={y2}
        stroke="currentColor"
        className={long ? 'text-cyan-500 dark:text-cyan-400' : 'text-zimon-border dark:text-slate-600'}
        strokeWidth={long ? 2 : 1}
        strokeLinecap="round"
      />
    )
  })

  if (compact) {
    return (
      <div className="flex h-full w-full min-w-[140px] max-w-[168px] flex-col items-center rounded-xl border border-zimon-border/70 bg-zimon-card/95 px-2 py-2 shadow-sm backdrop-blur-sm dark:border-cyan-500/15 dark:bg-slate-950/55 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.04),0_0_20px_-8px_rgba(34,211,238,0.15)]">
        <span className="text-center text-[8px] font-bold tracking-[0.08em] text-zimon-muted dark:text-cyan-200/55">
          FRAME RATE (FPS)
        </span>
        <div className="relative mt-0.5 h-[68px] w-[132px] shrink-0">
          <svg viewBox="0 0 120 72" className="h-full w-full">
            {tickEls}
            <path
              d={`M ${cx - rOuter} ${cy} A ${rOuter} ${rOuter} 0 0 1 ${cx + rOuter} ${cy}`}
              fill="none"
              stroke="currentColor"
              className="text-zimon-border/70 dark:text-slate-600"
              strokeWidth="7"
              strokeLinecap="round"
            />
            <path
              d={`M ${cx - rOuter} ${cy} A ${rOuter} ${rOuter} 0 0 1 ${cx + rOuter} ${cy}`}
              fill="none"
              stroke={`url(#fpsFill-${gid})`}
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={`${(angle / 180) * arcLen} ${arcLen}`}
            />
            <defs>
              <linearGradient id={`fpsFill-${gid}`} x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#22d3ee" />
                <stop offset="100%" stopColor="#06b6d4" />
              </linearGradient>
            </defs>
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-end pb-0 pt-3">
            <span className="text-xl font-bold tabular-nums leading-none text-zimon-fg dark:text-cyan-50">{fps}</span>
            <span className="text-[8px] font-medium text-zimon-muted">FPS</span>
          </div>
        </div>
        <div className="mt-1 flex w-full flex-wrap items-center justify-center gap-1">
          <button
            type="button"
            disabled={disabled || fps <= 1}
            onClick={() => onBump(-1)}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-zimon-border/70 bg-zimon-panel transition-all hover:border-cyan-400/40 active:scale-95 disabled:opacity-40 dark:border-cyan-500/20 dark:bg-slate-900/60"
          >
            <Minus className="h-3.5 w-3.5 text-zimon-fg" />
          </button>
          <button
            type="button"
            disabled={disabled || fps >= 120}
            onClick={() => onBump(1)}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-zimon-border/70 bg-zimon-panel transition-all hover:border-cyan-400/40 active:scale-95 disabled:opacity-40 dark:border-cyan-500/20 dark:bg-slate-900/60"
          >
            <Plus className="h-3.5 w-3.5 text-zimon-fg" />
          </button>
          <button
            type="button"
            disabled={disabled}
            onClick={() => void onApply()}
            className="rounded-lg bg-cyan-600 px-2.5 py-1 text-[9px] font-bold uppercase tracking-wide text-white shadow-sm shadow-cyan-500/20 transition-all hover:bg-cyan-500 active:scale-[0.98] disabled:opacity-40 dark:bg-cyan-500"
          >
            Apply
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex w-full max-w-[280px] flex-col items-center rounded-2xl border border-zimon-border/50 bg-zimon-card/80 px-4 py-4 shadow-inner shadow-black/5 backdrop-blur-md dark:border-cyan-500/15 dark:bg-slate-950/50 dark:shadow-[0_0_32px_-8px_rgba(34,211,238,0.12)]">
      <span className="text-[11px] font-bold uppercase tracking-wider text-zimon-muted dark:text-cyan-200/60">
        Frame rate (FPS)
      </span>
      <div className="relative mt-1 h-[110px] w-[200px]">
        <svg viewBox="0 0 120 72" className="h-full w-full">
          {tickEls}
          <path
            d={`M ${cx - rOuter} ${cy} A ${rOuter} ${rOuter} 0 0 1 ${cx + rOuter} ${cy}`}
            fill="none"
            stroke="currentColor"
            className="text-zimon-border/70"
            strokeWidth="7"
            strokeLinecap="round"
          />
          <path
            d={`M ${cx - rOuter} ${cy} A ${rOuter} ${rOuter} 0 0 1 ${cx + rOuter} ${cy}`}
            fill="none"
            stroke={`url(#fpsFill-${gid})`}
            strokeWidth="7"
            strokeLinecap="round"
            strokeDasharray={`${(angle / 180) * arcLen} ${arcLen}`}
          />
          <defs>
            <linearGradient id={`fpsFill-${gid}`} x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#22d3ee" />
              <stop offset="100%" stopColor="#06b6d4" />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1 pt-5">
          <span className="text-3xl font-bold tabular-nums text-zimon-fg">{fps}</span>
          <span className="text-[11px] font-medium text-zimon-muted">FPS</span>
        </div>
      </div>
      <div className="mt-3 flex w-full flex-wrap items-center justify-center gap-2">
        <button
          type="button"
          disabled={disabled || fps <= 1}
          onClick={() => onBump(-1)}
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-zimon-border bg-zimon-panel shadow-sm transition-all hover:border-cyan-400/35 active:scale-95 disabled:opacity-40 dark:border-cyan-500/20 dark:bg-slate-900/70"
        >
          <Minus className="h-5 w-5 text-zimon-fg" />
        </button>
        <span className="min-w-[2.25rem] text-center text-lg font-bold tabular-nums text-zimon-fg dark:text-cyan-100">
          {fps}
        </span>
        <button
          type="button"
          disabled={disabled || fps >= 120}
          onClick={() => onBump(1)}
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-zimon-border bg-zimon-panel shadow-sm transition-all hover:border-cyan-400/35 active:scale-95 disabled:opacity-40 dark:border-cyan-500/20 dark:bg-slate-900/70"
        >
          <Plus className="h-5 w-5 text-zimon-fg" />
        </button>
        <button
          type="button"
          disabled={disabled || fps >= 115}
          onClick={() => onBump(5)}
          className="rounded-xl border border-cyan-500/35 bg-cyan-500/10 px-3 py-2 text-xs font-bold text-cyan-700 transition-all hover:bg-cyan-500/15 active:scale-[0.98] disabled:opacity-40 dark:text-cyan-300"
        >
          +5
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={() => void onApply()}
          className="rounded-xl bg-cyan-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-cyan-500/25 transition-all hover:bg-cyan-500 active:scale-[0.98] disabled:opacity-40 dark:bg-cyan-500 dark:hover:bg-cyan-400"
        >
          Apply
        </button>
      </div>
    </div>
  )
}
