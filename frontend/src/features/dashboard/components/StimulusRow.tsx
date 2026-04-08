import { mapToPwm } from '../../../utils/pwm'
import type { StimState } from '../experimentPayload'

export function StimulusRow({
  title,
  s,
  setS,
  connected,
  onLiveSend,
}: {
  title: string
  s: StimState
  setS: (u: Partial<StimState>) => void
  connected: boolean
  onLiveSend: (pwm: number) => void
}) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-zimon-border/80 bg-zimon-card/50 px-3 py-2.5 sm:flex-row sm:flex-wrap sm:items-center sm:gap-x-3">
      <span className="text-sm font-medium text-zimon-fg w-36 shrink-0">{title}</span>
      <label className="flex items-center gap-2 text-xs text-zimon-muted">
        <input
          type="checkbox"
          className="rounded border-zimon-border"
          checked={s.enabled}
          onChange={(e) => {
            const en = e.target.checked
            setS({ enabled: en, intensity: en ? s.intensity : 0 })
            onLiveSend(en ? mapToPwm(s.intensity) : 0)
          }}
        />
        On
      </label>
      <input
        type="range"
        min={0}
        max={100}
        value={s.intensity}
        disabled={!s.enabled || !connected}
        onChange={(e) => {
          const n = Number(e.target.value)
          setS({ intensity: n })
          if (s.enabled) onLiveSend(mapToPwm(n))
        }}
        className="h-1.5 flex-1 min-w-[100px] accent-zimon-accent"
      />
      <span className="text-xs text-zimon-muted w-8">{s.intensity}%</span>
      <label className="flex items-center gap-1.5 text-xs text-zimon-muted">
        <input
          type="checkbox"
          checked={s.continuous}
          disabled={!s.enabled}
          onChange={(e) => {
            const c = e.target.checked
            setS({ continuous: c, durationMs: c ? 0 : s.durationMs, delayMs: c ? 0 : s.delayMs })
          }}
        />
        Hold
      </label>
    </div>
  )
}
