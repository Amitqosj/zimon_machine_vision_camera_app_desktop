import { useMemo } from 'react'

export type WellPlateSize = 12 | 24 | 48 | 96

const LAYOUT: Record<WellPlateSize, { rows: number; cols: number }> = {
  12: { rows: 4, cols: 3 },
  24: { rows: 4, cols: 6 },
  48: { rows: 6, cols: 8 },
  96: { rows: 8, cols: 12 },
}

type Props = {
  wells: WellPlateSize
  className?: string
}

/** Blueprint-style microplate diagram for the camera idle state. */
export function WellPlateSchematic({ wells, className = '' }: Props) {
  const { rows, cols } = LAYOUT[wells]

  const circles = useMemo(() => {
    const vbW = 280
    const vbH = 188
    const padX = 28
    const padY = 22
    const innerW = vbW - padX * 2
    const innerH = vbH - padY * 2
    const cellW = innerW / cols
    const cellH = innerH / rows
    const r = Math.min(cellW, cellH) * 0.36
    const out: { cx: number; cy: number; key: string }[] = []
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const cx = padX + col * cellW + cellW / 2
        const cy = padY + row * cellH + cellH / 2
        out.push({ cx, cy, key: `${row}-${col}` })
      }
    }
    return { vbW, vbH, r, circles: out }
  }, [rows, cols])

  return (
    <div className={['flex flex-col items-center gap-2', className].filter(Boolean).join(' ')}>
      <svg
        viewBox={`0 0 ${circles.vbW} ${circles.vbH}`}
        className="h-auto w-full max-w-[min(100%,420px)] text-cyan-400/50 drop-shadow-[0_0_28px_rgba(34,211,238,0.12)]"
        aria-hidden
      >
        <defs>
          <linearGradient id="wellPlateEdge" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgba(56, 189, 248, 0.45)" />
            <stop offset="100%" stopColor="rgba(14, 165, 233, 0.2)" />
          </linearGradient>
        </defs>
        <rect
          x="6"
          y="6"
          width={circles.vbW - 12}
          height={circles.vbH - 12}
          rx="14"
          ry="14"
          fill="#020617"
          stroke="url(#wellPlateEdge)"
          strokeWidth="1.5"
        />
        {circles.circles.map((c) => (
          <circle
            key={c.key}
            cx={c.cx}
            cy={c.cy}
            r={circles.r}
            fill="rgba(15, 23, 42, 0.9)"
            stroke="rgba(34, 211, 238, 0.35)"
            strokeWidth="1"
          />
        ))}
      </svg>
      <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-cyan-200/70 dark:text-cyan-300/60">
        {wells}-well plate
      </p>
    </div>
  )
}

export function normalizeWellPlateSize(n: number): WellPlateSize {
  if (n === 12 || n === 24 || n === 48 || n === 96) return n
  return 96
}
