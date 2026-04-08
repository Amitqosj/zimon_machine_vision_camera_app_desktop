import { Camera, Cog, Thermometer } from 'lucide-react'
import { useApiHealthOnline } from '../../hooks/useApiHealthOnline'

export type AuthStatusBarMode = 'login-card' | 'splash-dock'

type Props = {
  /**
   * login-card: inside auth card footer — ZIMON strip + Camera / Chamber / Temperature.
   * splash-dock: fixed to viewport bottom on boot / logo screen (dark glass).
   */
  mode: AuthStatusBarMode
}

function StatusDot({ active }: { active: boolean }) {
  if (!active) return null
  return (
    <span
      className="relative ml-0.5 inline-flex h-2 w-2 shrink-0"
      aria-hidden
    >
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/50" />
      <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.7)]" />
    </span>
  )
}

/**
 * Hardware-style status: Camera reflects API health (backend + camera service).
 * Shown on login card and splash screen only.
 */
export function AuthStatusBar({ mode }: Props) {
  const online = useApiHealthOnline()

  const cameraLabel = online === null ? '…' : online ? 'Connected' : 'Offline'
  const cameraClass =
    online === null ? 'text-slate-600' : online ? 'text-emerald-700' : 'text-amber-700'
  const tempClass =
    online === false ? 'text-amber-700' : 'font-semibold text-emerald-700'

  const cameraBlock = (
    <div className="flex items-center justify-center gap-2">
      <Camera
        className={`h-4 w-4 shrink-0 ${mode === 'splash-dock' ? 'text-slate-300' : 'text-slate-600'}`}
        strokeWidth={1.75}
        aria-hidden
      />
      <span className={mode === 'splash-dock' ? 'text-slate-400' : 'text-slate-600'}>
        Camera
      </span>
      <span className={`flex items-center gap-1 font-semibold ${cameraClass}`}>
        {cameraLabel}
        <StatusDot active={online === true} />
      </span>
    </div>
  )

  const chamberBlock = (
    <div className="flex items-center justify-center gap-2">
      <Cog
        className={`h-4 w-4 shrink-0 ${mode === 'splash-dock' ? 'text-cyan-400/90' : 'text-blue-800/80'}`}
        strokeWidth={1.75}
        aria-hidden
      />
      <span className={mode === 'splash-dock' ? 'text-slate-400' : 'text-slate-600'}>
        Chamber
      </span>
      <span
        className={`font-semibold ${mode === 'splash-dock' ? 'text-sky-300' : 'text-blue-800'}`}
      >
        Idle
      </span>
    </div>
  )

  const tempBlock = (
    <div className="flex items-center justify-center gap-2">
      <Thermometer
        className={`h-4 w-4 shrink-0 ${mode === 'splash-dock' ? 'text-slate-400' : 'text-slate-600'}`}
        strokeWidth={1.75}
        aria-hidden
      />
      <span className={mode === 'splash-dock' ? 'text-slate-400' : 'text-slate-600'}>
        Temperature
      </span>
      <span className={tempClass}>{online === false ? '—' : 'OK'}</span>
    </div>
  )

  if (mode === 'splash-dock') {
    return (
      <div
        className="pointer-events-none fixed bottom-0 left-0 right-0 z-50 border-t border-white/[0.08] bg-zimon-card/95 px-3 py-3 shadow-[0_-12px_40px_rgba(0,0,0,0.45)] backdrop-blur-md sm:px-6"
        role="status"
        aria-live="polite"
        aria-label="ZIMON hardware status"
      >
        <div className="mx-auto flex max-w-3xl flex-col items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-6">
          <div className="flex items-center justify-center gap-2 border-b border-white/[0.06] pb-2 sm:border-b-0 sm:pb-0">
            <span className="text-sm font-bold tracking-[0.28em] text-white">ZIMON</span>
            <span className="hidden text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500 sm:inline">
              System
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-[11px] font-semibold tracking-wide text-slate-200 sm:flex sm:flex-1 sm:justify-end sm:gap-8 sm:text-xs">
            <div className="flex min-w-0 flex-col items-center gap-1 sm:flex-row sm:gap-2">
              {cameraBlock}
            </div>
            <div className="flex min-w-0 flex-col items-center gap-1 border-x border-white/[0.06] sm:flex-row sm:border-x-0 sm:gap-2">
              {chamberBlock}
            </div>
            <div className="flex min-w-0 flex-col items-center gap-1 sm:flex-row sm:gap-2">
              {tempBlock}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // login-card
  return (
    <div className="border-t border-slate-200" role="status" aria-live="polite">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200 bg-gradient-to-r from-slate-50 via-white to-slate-50 px-4 py-2.5 sm:px-5">
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold tracking-[0.24em] text-[#1e3a5f]">ZIMON</span>
          <span className="hidden h-4 w-px bg-slate-200 sm:block" aria-hidden />
          <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-500">
            Hardware status
          </span>
        </div>
        <span className="text-[10px] text-slate-500">Camera · Chamber · Environment</span>
      </div>
      <div className="grid grid-cols-3 bg-gradient-to-b from-slate-50 to-slate-100 text-[11px] font-semibold tracking-wide text-slate-700 sm:text-xs">
        <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-200/80 py-3.5 px-2 sm:flex-row sm:gap-2 sm:py-4">
          {cameraBlock}
        </div>
        <div className="flex flex-col items-center justify-center gap-1 border-r border-slate-200/80 py-3.5 px-2 sm:flex-row sm:gap-2 sm:py-4">
          {chamberBlock}
        </div>
        <div className="flex flex-col items-center justify-center gap-1 py-3.5 px-2 sm:flex-row sm:gap-2 sm:py-4">
          {tempBlock}
        </div>
      </div>
    </div>
  )
}
