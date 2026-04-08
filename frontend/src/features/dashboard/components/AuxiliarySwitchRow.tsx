type Props = {
  icon: React.ReactNode
  label: string
  checked: boolean
  disabled?: boolean
  onChange: (on: boolean) => void
  compact?: boolean
}

export function AuxiliarySwitchRow({ icon, label, checked, disabled, onChange, compact }: Props) {
  if (compact) {
    return (
      <div className="flex items-center justify-between gap-2 rounded-lg border border-zimon-border/60 bg-zimon-card/80 px-2 py-1.5 shadow-sm backdrop-blur-sm transition-colors hover:border-cyan-400/30 dark:border-cyan-500/10 dark:bg-slate-950/45 dark:hover:border-cyan-400/20">
        <div className="flex min-w-0 items-center gap-2">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-zimon-border/40 bg-zimon-panel text-sm dark:border-cyan-500/10 dark:bg-slate-900/70">
            {icon}
          </span>
          <span className="truncate text-[11px] font-semibold text-zimon-fg">{label}</span>
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={checked}
          disabled={disabled}
          onClick={() => onChange(!checked)}
          className={[
            'relative h-6 w-11 shrink-0 rounded-full border transition-all duration-200',
            checked
              ? 'border-emerald-400/40 bg-emerald-600 shadow-[0_0_10px_-2px_rgba(52,211,153,0.5)]'
              : 'border-slate-600 bg-slate-800',
            disabled ? 'opacity-40' : 'active:scale-95',
          ].join(' ')}
        >
          <span
            className={[
              'absolute top-0.5 h-5 w-5 rounded-full bg-white shadow ring-1 ring-black/10 transition-transform duration-200',
              checked ? 'left-[1.375rem]' : 'left-0.5',
            ].join(' ')}
          />
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-zimon-border/50 bg-zimon-card/70 px-4 py-3 shadow-sm backdrop-blur-md transition-colors hover:border-cyan-400/20 dark:border-cyan-500/10 dark:bg-slate-950/45 dark:hover:border-cyan-400/15">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl border border-zimon-border/40 bg-zimon-panel text-xl shadow-inner dark:border-cyan-500/10 dark:bg-slate-900/60">
          {icon}
        </span>
        <span className="text-sm font-semibold text-zimon-fg">{label}</span>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={[
          'relative h-9 w-[3.25rem] shrink-0 rounded-full border transition-all duration-200',
          checked
            ? 'border-emerald-400/40 bg-emerald-500/90 shadow-[0_0_16px_-2px_rgba(52,211,153,0.55)]'
            : 'border-zimon-border/80 bg-zimon-border/60 dark:border-slate-600 dark:bg-slate-800',
          disabled ? 'opacity-40' : 'active:scale-95',
        ].join(' ')}
      >
        <span
          className={[
            'absolute top-1 h-7 w-7 rounded-full bg-white shadow-md ring-1 ring-black/5 transition-transform duration-200',
            checked ? 'left-7' : 'left-1',
          ].join(' ')}
        />
      </button>
    </div>
  )
}
