import { mapToPwm } from '../../../utils/pwm'

type Props = {
  title: string
  spec: string
  icon: React.ReactNode
  active: boolean
  intensity: number
  connected: boolean
  accent: 'ir' | 'white' | 'rgb'
  onToggle: (on: boolean) => void
  onIntensity: (v: number) => void
  colorExtra?: React.ReactNode
  /** Short horizontal deck: small card, tight padding (control panel center column). */
  compact?: boolean
}

const ring = {
  ir: 'border-red-400/45 shadow-[0_0_24px_-4px_rgba(248,113,113,0.35)] dark:border-red-400/35',
  white: 'border-amber-300/50 shadow-[0_0_24px_-4px_rgba(251,191,36,0.2)] dark:border-amber-400/30',
  rgb: 'border-violet-400/45 shadow-[0_0_24px_-4px_rgba(167,139,250,0.35)] dark:border-violet-400/35',
}

export function LightingToggleCard({
  title,
  spec,
  icon,
  active,
  intensity,
  connected,
  accent,
  onToggle,
  onIntensity,
  colorExtra,
  compact,
}: Props) {
  if (compact) {
    return (
      <div
        className={[
          'flex w-full flex-col rounded-lg border bg-zimon-card/90 p-1.5 text-left shadow-sm backdrop-blur-sm transition-all duration-200 dark:bg-slate-950/50',
          active
            ? `ring-1 ring-cyan-400/25 ${ring[accent]}`
            : 'border-zimon-border/60 dark:border-cyan-500/10',
          connected
            ? 'cursor-pointer hover:border-cyan-400/30 dark:hover:border-cyan-400/15'
            : 'opacity-50',
        ].join(' ')}
        onClick={() => connected && onToggle(!active)}
        onKeyDown={(e) => {
          if (!connected) return
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            onToggle(!active)
          }
        }}
        role="button"
        tabIndex={connected ? 0 : -1}
      >
        <div className="flex gap-1.5">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-zimon-border/50 bg-zimon-panel dark:border-cyan-500/10 dark:bg-slate-900/70">
            {icon}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-1">
              <div className="min-w-0">
                <div className="text-[9px] font-bold leading-tight text-zimon-fg">{title}</div>
                <div className="text-[8px] leading-tight text-zimon-muted">{spec}</div>
              </div>
              <span
                className={[
                  'shrink-0 rounded px-1 py-0.5 text-[7px] font-bold uppercase',
                  !connected
                    ? 'bg-zimon-border/40 text-zimon-muted'
                    : active
                      ? 'bg-cyan-500/20 text-cyan-700 dark:text-cyan-300'
                      : 'bg-slate-800/80 text-zimon-muted',
                ].join(' ')}
              >
                {!connected ? 'N/C' : active ? 'On' : 'Off'}
              </span>
            </div>
            {active ? (
              <div className="mt-1" onClick={(e) => e.stopPropagation()}>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={intensity}
                  disabled={!connected}
                  onChange={(e) => onIntensity(Number(e.target.value))}
                  className="h-1 w-full accent-cyan-500 dark:accent-cyan-400"
                />
              </div>
            ) : (
              <div className="mt-1 h-1" aria-hidden />
            )}
            {colorExtra ? (
              <div className="mt-0.5" onClick={(e) => e.stopPropagation()}>
                {colorExtra}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      className={[
        'flex min-h-[148px] w-full flex-col items-center justify-between rounded-2xl border bg-zimon-card/90 p-3 text-center shadow-md backdrop-blur-sm transition-all duration-200 dark:bg-slate-950/40',
        active
          ? `ring-2 ring-cyan-400/20 ${ring[accent]}`
          : 'border-zimon-border/70 dark:border-cyan-500/10',
        connected
          ? 'cursor-pointer hover:-translate-y-0.5 hover:border-cyan-400/25 hover:shadow-lg dark:hover:border-cyan-400/20'
          : 'opacity-50',
      ].join(' ')}
      onClick={() => connected && onToggle(!active)}
      onKeyDown={(e) => {
        if (!connected) return
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onToggle(!active)
        }
      }}
      role="button"
      tabIndex={connected ? 0 : -1}
    >
      <div className="flex w-full items-start justify-between gap-2">
        <div className="flex min-w-0 flex-1 flex-col items-center">
          <div className="mb-1 flex h-11 w-11 items-center justify-center rounded-xl border border-zimon-border/50 bg-zimon-panel/80 dark:border-cyan-500/10 dark:bg-slate-900/50">
            {icon}
          </div>
          <div className="text-xs font-bold text-zimon-fg">{title}</div>
          <div className="mt-0.5 text-[10px] text-zimon-muted">{spec}</div>
        </div>
        <span
          className={[
            'shrink-0 rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide',
            !connected
              ? 'bg-zimon-border/40 text-zimon-muted'
              : active
                ? 'border border-cyan-500/30 bg-cyan-500/15 text-cyan-700 dark:text-cyan-300'
                : 'border border-zimon-border/60 bg-zimon-card text-zimon-muted dark:border-slate-600 dark:bg-slate-900/50',
          ].join(' ')}
        >
          {!connected ? 'N/C' : active ? 'On' : 'Off'}
        </span>
      </div>
      {active ? (
        <div className="w-full" onClick={(e) => e.stopPropagation()}>
          <div className="text-[10px] font-semibold text-cyan-600 dark:text-cyan-400">{intensity}% intensity</div>
          <input
            type="range"
            min={0}
            max={100}
            value={intensity}
            disabled={!connected}
            onChange={(e) => onIntensity(Number(e.target.value))}
            className="mt-1 h-1.5 w-full accent-cyan-500 dark:accent-cyan-400"
          />
        </div>
      ) : (
        <span className="text-[10px] text-zimon-muted">{connected ? 'Tap to enable' : 'No link'}</span>
      )}
      {colorExtra ? (
        <div className="mt-1 w-full" onClick={(e) => e.stopPropagation()}>
          {colorExtra}
        </div>
      ) : null}
    </div>
  )
}

export function sendLightingPwm(
  channel: 'IR' | 'WHITE',
  on: boolean,
  intensity: number,
  sendCmd: (cmd: string) => void,
) {
  const pwm = on ? mapToPwm(intensity) : 0
  void sendCmd(`${channel === 'IR' ? 'IR' : 'WHITE'} ${pwm}`)
}
