import { Check, Play, Plus, X } from 'lucide-react'

type Props = {
  previewOn: boolean
  hasCamera: boolean
  connectedVisual: boolean
  elapsedRatio: number
  timerLabel: string
  durationS: number
  onTogglePreview: () => void
  onStopPreview: () => void
  onPlayPreview: () => void
  onBumpDuration: (delta: number) => void
  disabled?: boolean
  /** When nested inside the live camera card, flattens outer chrome to avoid double borders. */
  className?: string
}

/** Single compact horizontal bar: label, toggle, progress, time, play, stop, duration. */
export function CameraPreviewBar({
  previewOn,
  hasCamera,
  connectedVisual,
  elapsedRatio,
  timerLabel,
  durationS,
  onTogglePreview,
  onStopPreview,
  onPlayPreview,
  onBumpDuration,
  disabled,
  className,
}: Props) {
  const pct = Math.round(Math.min(1, Math.max(0, elapsedRatio)) * 100)

  return (
    <div
      className={[
        'flex min-h-[2.75rem] flex-wrap items-center gap-x-2 gap-y-2 overflow-x-auto rounded-xl border border-zimon-border/60 bg-zimon-card/90 py-2 pl-2.5 pr-2.5 shadow-sm backdrop-blur-sm dark:border-cyan-500/12 dark:bg-slate-950/70 dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.04)]',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <span className="shrink-0 text-[11px] font-semibold tracking-tight text-zimon-fg dark:text-cyan-100/85">
        Camera Preview
      </span>

      <span className="hidden h-4 w-px shrink-0 bg-zimon-border/70 sm:block dark:bg-cyan-500/15" aria-hidden />

      <div className="flex shrink-0 items-center gap-1.5">
        <button
          type="button"
          role="switch"
          aria-checked={previewOn}
          aria-label={previewOn ? 'Disable preview' : 'Enable preview'}
          disabled={disabled || !hasCamera}
          onClick={() => onTogglePreview()}
          className={[
            'relative h-5 w-9 shrink-0 rounded-full border transition-all duration-200',
            previewOn
              ? 'border-cyan-400/45 bg-cyan-600 shadow-[0_0_10px_-2px_rgba(34,211,238,0.45)] dark:bg-cyan-500'
              : 'border-zimon-border bg-zimon-border/80 dark:border-slate-600 dark:bg-slate-800',
            disabled || !hasCamera ? 'opacity-40' : 'active:scale-95',
          ].join(' ')}
        >
          <span
            className={[
              'absolute top-0.5 h-4 w-4 rounded-full bg-white shadow-sm ring-1 ring-black/5 transition-transform duration-200',
              previewOn ? 'left-4' : 'left-0.5',
            ].join(' ')}
          />
        </button>
        {connectedVisual ? (
          <Check className="h-3.5 w-3.5 shrink-0 text-emerald-500 dark:text-emerald-400" strokeWidth={2.5} aria-hidden />
        ) : null}
      </div>

      <div
        className="relative h-1.5 min-w-[72px] flex-1 overflow-hidden rounded-full bg-zimon-border/50 dark:bg-slate-800/90"
        title="Session progress"
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-cyan-600 to-cyan-400 transition-[width] duration-300 dark:from-cyan-500 dark:to-cyan-300"
          style={{ width: `${pct}%` }}
        />
      </div>

      <span
        className="shrink-0 font-mono text-[11px] font-semibold tabular-nums tracking-tight text-zimon-fg dark:text-cyan-50/90"
        title="Elapsed / session"
      >
        {timerLabel}
      </span>

      <div className="flex shrink-0 items-center gap-0.5 border-l border-zimon-border/50 pl-2 dark:border-cyan-500/12">
        <button
          type="button"
          disabled={disabled || !hasCamera}
          onClick={() => void onPlayPreview()}
          className="flex h-7 w-7 items-center justify-center rounded-lg bg-cyan-600 text-white shadow-sm shadow-cyan-500/20 transition-all hover:bg-cyan-500 active:scale-95 disabled:opacity-40 dark:bg-cyan-500 dark:hover:bg-cyan-400"
          title={previewOn ? 'Stream active' : 'Start preview'}
        >
          <Play className="h-3.5 w-3.5 fill-current" />
        </button>
      </div>

      <div className="flex shrink-0 items-center gap-1 border-l border-zimon-border/50 pl-2 dark:border-cyan-500/12">
        <button
          type="button"
          onClick={() => onBumpDuration(60)}
          className="flex h-7 w-7 items-center justify-center rounded-lg text-zimon-muted transition-colors hover:bg-zimon-panel/80 hover:text-zimon-fg active:scale-95 dark:hover:bg-slate-800/80"
          title="Add 60s to duration cap"
        >
          <Plus className="h-3.5 w-3.5" strokeWidth={2.2} />
        </button>
        <span className="hidden text-[9px] text-zimon-muted sm:inline" title="Recording duration cap">
          {durationS}s
        </span>
        <button
          type="button"
          disabled={!previewOn}
          onClick={() => onStopPreview()}
          className="flex h-7 w-7 items-center justify-center rounded-lg border border-red-400/35 text-red-600 transition-colors hover:bg-red-500/10 active:scale-95 disabled:opacity-30 dark:border-red-500/35 dark:text-red-400"
          title="Stop preview"
        >
          <X className="h-3.5 w-3.5" strokeWidth={2.2} />
        </button>
      </div>
    </div>
  )
}
