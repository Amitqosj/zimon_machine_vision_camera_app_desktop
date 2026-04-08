import { useCallback, useState } from 'react'
import { mapToPwm } from '../../../utils/pwm'

export function LightingRow({
  label,
  connected,
  onSend,
  onLevelChange,
}: {
  label: string
  connected: boolean
  onSend: (pwm: number) => void
  onLevelChange?: (level: number) => void
}) {
  const [enabled, setEnabled] = useState(false)
  const [v, setV] = useState(0)

  const apply = useCallback(
    (nextEn: boolean, nextV: number) => {
      if (!connected) return
      const pwm = nextEn ? mapToPwm(nextV) : 0
      onSend(pwm)
      onLevelChange?.(nextEn ? nextV : 0)
    },
    [connected, onSend, onLevelChange],
  )

  return (
    <div className="flex flex-col gap-2 rounded-xl border border-zimon-border/80 bg-zimon-card/50 p-3 sm:flex-row sm:items-center sm:gap-3">
      <span className="text-sm font-medium text-zimon-fg w-28 shrink-0">{label}</span>
      <label className="flex items-center gap-2 text-xs text-zimon-muted">
        <input
          type="checkbox"
          className="rounded border-zimon-border"
          checked={enabled}
          onChange={(e) => {
            const en = e.target.checked
            setEnabled(en)
            if (!en) setV(0)
            apply(en, en ? v : 0)
          }}
        />
        On
      </label>
      <input
        type="range"
        min={0}
        max={100}
        value={v}
        disabled={!enabled || !connected}
        onChange={(e) => {
          const n = Number(e.target.value)
          setV(n)
          apply(true, n)
        }}
        className="h-1.5 flex-1 accent-zimon-accent"
      />
      <span className="text-xs text-zimon-muted w-8">{v}%</span>
    </div>
  )
}
