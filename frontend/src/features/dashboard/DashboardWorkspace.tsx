import {
  Maximize2,
  Minimize2,
  Palette,
  Pause,
  Play,
  Square,
  SunMedium,
  Video,
  Waves,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { CameraLivePreview } from '../../components/CameraLivePreview'
import { useZimonWorkspace } from '../../context/ZimonWorkspaceContext'
import { mapToPwm } from '../../utils/pwm'
import type { ZimonProtocol } from '../../types/zimonProtocol'
import { loadProtocolLibrary } from '../protocol-builder/protocolStorage'
import { AuxiliarySwitchRow } from './components/AuxiliarySwitchRow'
import { CameraPreviewBar } from './components/CameraPreviewBar'
import { normalizeWellPlateSize, WellPlateSchematic } from './components/WellPlateSchematic'
import { FpsGaugePanel } from './components/FpsGaugePanel'
import { LightingToggleCard, sendLightingPwm } from './components/LightingToggleCard'
import { useDashboardArduino } from './hooks/useDashboardArduino'
import { useDashboardCamera } from './hooks/useDashboardCamera'
import { useDashboardExperiment } from './hooks/useDashboardExperiment'

type Props = {
  plateWells: number
  variant?: 'adult' | 'larval'
}

function hardwareDot(ok: boolean, warn: boolean) {
  if (ok) return 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.7)]'
  if (warn) return 'bg-amber-400'
  return 'bg-red-500/80'
}

export function DashboardWorkspace({ plateWells, variant = 'adult' }: Props) {
  const isLarval = variant === 'larval'
  const videoRef = useRef<HTMLDivElement>(null)
  const [fs, setFs] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const ws = useZimonWorkspace()
  const camApi = useDashboardCamera()
  const ard = useDashboardArduino()
  const exp = useDashboardExperiment(camApi.cam)

  const [ir, setIr] = useState({ on: false, v: 45 })
  const [white, setWhite] = useState({ on: false, v: 50 })
  const [water, setWater] = useState({ on: false, v: 65 })
  const [sideCamera, setSideCamera] = useState('')
  const [library, setLibrary] = useState(() => loadProtocolLibrary())

  const camRef = useRef(camApi)
  camRef.current = camApi
  const expRef = useRef(exp)
  expRef.current = exp

  useEffect(() => {
    const h = (e: Event) => {
      const d = (e as CustomEvent<{ durationS: number; fps: number }>).detail
      if (!d) return
      camRef.current.setFps(d.fps)
      expRef.current.setDurationS(d.durationS)
      void camRef.current.applyFps()
    }
    window.addEventListener('zimon-apply-recipe', h as EventListener)
    return () => window.removeEventListener('zimon-apply-recipe', h as EventListener)
  }, [])

  useEffect(() => {
    if (!ws.activeProtocol?.phases.length) return
    const total = ws.activeProtocol.phases.reduce((s, p) => s + p.durationS, 0)
    if (total > 0) exp.setDurationS(total)
  }, [ws.activeProtocol, exp.setDurationS])

  useEffect(() => {
    if (!exp.running || !ws.activeProtocol?.phases.length) {
      ws.setCurrentPhaseLabel(exp.running ? 'Recording' : 'Idle')
      return
    }
    const phases = ws.activeProtocol.phases
    const id = window.setInterval(() => {
      const ts = exp.startTs
      if (!ts) return
      const elapsed = (Date.now() - ts) / 1000
      let acc = 0
      for (const ph of phases) {
        acc += ph.durationS
        if (elapsed < acc) {
          ws.setCurrentPhaseLabel(ph.label || ph.kind)
          return
        }
      }
      ws.setCurrentPhaseLabel('Complete')
    }, 500)
    return () => window.clearInterval(id)
  }, [exp.running, exp.startTs, ws.activeProtocol, ws.setCurrentPhaseLabel])

  const applyIr = useCallback(
    (next: { on: boolean; v: number }) => {
      const v = next.on && next.v < 5 ? 40 : next.v
      setIr({ on: next.on, v })
      sendLightingPwm('IR', next.on, v, ard.sendCmd)
    },
    [ard.sendCmd],
  )

  const applyWhite = useCallback(
    (next: { on: boolean; v: number }) => {
      const v = next.on && next.v < 5 ? 45 : next.v
      setWhite({ on: next.on, v })
      sendLightingPwm('WHITE', next.on, v, ard.sendCmd)
    },
    [ard.sendCmd],
  )

  const applyWater = useCallback(
    (next: { on: boolean; v: number }) => {
      const v = next.on && next.v < 5 ? 60 : next.v
      setWater({ on: next.on, v })
      if (!ard.arduinoOk) return
      const pwm = next.on ? mapToPwm(v) : 0
      void ard.sendCmd(`PUMP ${pwm}`)
      ard.setPumpLevel(next.on ? v : 0)
    },
    [ard],
  )

  const toggleFs = useCallback(async () => {
    const el = videoRef.current
    if (!el) return
    try {
      if (!document.fullscreenElement) {
        await el.requestFullscreen()
        setFs(true)
      } else {
        await document.exitFullscreen()
        setFs(false)
      }
    } catch {
      setFs(!!document.fullscreenElement)
    }
  }, [])

  useEffect(() => {
    const onFs = () => setFs(!!document.fullscreenElement)
    document.addEventListener('fullscreenchange', onFs)
    return () => document.removeEventListener('fullscreenchange', onFs)
  }, [])

  const lightingPill = useMemo(() => {
    const parts = [ir.on ? ir.v : 0, white.on ? white.v : 0, exp.rgbOn ? exp.rgbIntensityPct : 0]
    const m = Math.max(...parts, 0)
    return m > 0 ? `Intensity ${m}%` : 'Lights off'
  }, [ir, white, exp.rgbOn, exp.rgbIntensityPct])

  const wellSize = normalizeWellPlateSize(plateWells)
  const showCameraStream = camApi.previewOn && camApi.cam

  const experimentStatus = useMemo(() => {
    if (exp.running) return 'Running' as const
    if (!ard.arduinoOk || !camApi.cam) return 'Idle' as const
    return 'Ready' as const
  }, [exp.running, ard.arduinoOk, camApi.cam])

  const arduinoOk = ard.arduinoOk
  const systemReady = arduinoOk && !!camApi.cam

  const protocolTotalS = useMemo(() => {
    if (!ws.activeProtocol?.phases.length) return 0
    return ws.activeProtocol.phases.reduce((s, p) => s + p.durationS, 0)
  }, [ws.activeProtocol])

  const phaseWidths = useMemo(() => {
    const p = ws.activeProtocol
    if (!p?.phases.length) {
      return [
        { label: 'Baseline', pct: 33.33, kind: 'baseline' as const },
        { label: 'Stimulus', pct: 33.34, kind: 'stimulus' as const },
        { label: 'Recovery', pct: 33.33, kind: 'recovery' as const },
      ]
    }
    const t = p.phases.reduce((s, x) => s + x.durationS, 0) || 1
    return p.phases.map((ph) => ({
      label: ph.label || ph.kind,
      pct: (ph.durationS / t) * 100,
      kind: ph.kind,
    }))
  }, [ws.activeProtocol])

  const cameraListForRun = useMemo(() => {
    const top = camApi.cam
    if (!top) return [] as string[]
    if (isLarval || !sideCamera || sideCamera === top) return [top]
    return [top, sideCamera]
  }, [camApi.cam, sideCamera, isLarval])

  const onStart = async () => {
    const id = `EX-${Date.now().toString(36).toUpperCase()}`
    ws.setExperimentRunId(id)
    ws.appendActionLog(`Start experiment ${id} (${ws.activeProtocol?.name || 'no protocol'})`)
    ws.setCurrentPhaseLabel('Recording')
    await exp.startExperiment(plateWells, cameraListForRun)
  }

  const onStop = async () => {
    ws.appendActionLog('Stop experiment')
    ws.setExperimentRunId(null)
    await exp.stopExperiment()
    ws.setCurrentPhaseLabel('Idle')
  }

  const refreshLibrary = () => setLibrary(loadProtocolLibrary())

  const onPickSavedProtocol = (id: string) => {
    const p = library.find((x) => x.id === id)
    ws.setActiveProtocol(p ?? null)
    if (p?.phases.length) {
      const total = p.phases.reduce((s, ph) => s + ph.durationS, 0)
      if (total > 0) exp.setDurationS(total)
    }
  }

  const onLoadProtocolFile = async (f: File | null) => {
    if (!f) return
    try {
      const raw = JSON.parse(await f.text()) as ZimonProtocol
      if (!raw.id || !raw.name || !Array.isArray(raw.phases)) throw new Error('Invalid protocol file')
      ws.setActiveProtocol(raw)
      ws.appendActionLog(`Loaded protocol file: ${raw.name}`)
      const total = raw.phases.reduce((s, ph) => s + ph.durationS, 0)
      if (total > 0) exp.setDurationS(total)
    } catch {
      ws.appendActionLog('Failed to parse protocol JSON')
    }
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const sideOptions = camApi.cameras.filter((c) => c !== camApi.cam)

  return (
    <div className="flex flex-col gap-4">
      <input
        ref={fileInputRef}
        type="file"
        accept="application/json,.json"
        className="hidden"
        onChange={(e) => void onLoadProtocolFile(e.target.files?.[0] ?? null)}
      />

      {/* Module header */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-cyan-500/20 bg-slate-950/50 px-4 py-3 dark:bg-slate-950/60">
        <div className="flex min-w-0 flex-wrap items-center gap-3">
          <span
            className={[
              'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide',
              experimentStatus === 'Running'
                ? 'border-sky-500/40 bg-sky-500/15 text-sky-300'
                : experimentStatus === 'Ready'
                  ? 'border-emerald-500/35 bg-emerald-500/10 text-emerald-300'
                  : 'border-white/10 bg-white/5 text-slate-400',
            ].join(' ')}
          >
            <span
              className={[
                'h-2 w-2 rounded-full',
                experimentStatus === 'Running' ? 'animate-pulse bg-red-500' : 'bg-slate-500',
              ].join(' ')}
            />
            {experimentStatus}
          </span>
          <div className="min-w-0 text-xs">
            <span className="text-zimon-muted">Protocol </span>
            <span className="font-semibold text-zimon-fg">{ws.activeProtocol?.name || '—'}</span>
          </div>
          <div className="text-xs tabular-nums">
            <span className="text-zimon-muted">Run ID </span>
            <span className="font-mono text-cyan-200/90">{ws.experimentRunId || '—'}</span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-wide">
          <span className="text-zimon-muted">System</span>
          <span
            className={systemReady ? 'text-emerald-400' : 'text-amber-400'}
            title={systemReady ? 'Arduino and primary camera available' : 'Check connections'}
          >
            {systemReady ? 'Ready' : 'Not ready'}
          </span>
        </div>
      </div>

      {camApi.err || exp.err ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-600 dark:text-red-300">
          {camApi.err || exp.err}
        </div>
      ) : null}

      {!arduinoOk ? (
        <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-800 dark:text-amber-200/90">
          Arduino not connected — use Settings to connect the serial port. Lighting and auxiliary controls need the
          link.
        </p>
      ) : null}

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        {/* Left column */}
        <aside className="xl:col-span-3 space-y-3">
          <div className="rounded-xl border border-zimon-border/70 bg-zimon-card/40 p-3 dark:border-cyan-500/15 dark:bg-slate-950/40">
            <h3 className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted dark:text-cyan-200/55">
              Protocol
            </h3>
            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 py-2 text-xs font-semibold text-cyan-100 transition-colors hover:bg-cyan-500/20"
              >
                Load protocol file…
              </button>
              <div className="flex gap-2">
                <select
                  className="min-w-0 flex-1 rounded-lg border border-zimon-border bg-slate-900/60 px-2 py-2 text-xs dark:border-cyan-500/20"
                  value={ws.activeProtocol?.id ?? ''}
                  onChange={(e) => onPickSavedProtocol(e.target.value)}
                >
                  <option value="">Saved in browser…</option>
                  {library.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={refreshLibrary}
                  className="shrink-0 rounded-lg border border-zimon-border px-2 py-2 text-xs dark:border-cyan-500/20"
                >
                  ↻
                </button>
              </div>
              <Link
                to="/app/protocol-builder"
                className="text-center text-[11px] font-medium text-cyan-400/90 underline-offset-2 hover:underline"
              >
                Open Protocol Builder
              </Link>
            </div>
            {ws.activeProtocol ? (
              <p className="mt-2 line-clamp-4 text-[11px] leading-relaxed text-zimon-muted">
                {ws.activeProtocol.description || 'No description'}
              </p>
            ) : null}
            {protocolTotalS > 0 ? (
              <p className="mt-1 text-[10px] text-cyan-200/70">Timeline total: {protocolTotalS}s</p>
            ) : null}
          </div>

          <div className="rounded-xl border border-zimon-border/70 bg-zimon-card/40 p-3 dark:border-cyan-500/15 dark:bg-slate-950/40">
            <h3 className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted dark:text-cyan-200/55">
              Cameras
            </h3>
            <label className="mb-1 block text-[10px] text-zimon-muted">Top (live preview)</label>
            <select
              className="mb-2 w-full rounded-lg border border-zimon-border bg-slate-900/60 px-2 py-2 text-xs dark:border-cyan-500/20"
              value={camApi.cam}
              onChange={(e) => camApi.setCam(e.target.value)}
            >
              {camApi.cameras.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            {!isLarval && sideOptions.length > 0 ? (
              <>
                <label className="mb-1 block text-[10px] text-zimon-muted">Side (also record)</label>
                <select
                  className="w-full rounded-lg border border-zimon-border bg-slate-900/60 px-2 py-2 text-xs dark:border-cyan-500/20"
                  value={sideCamera}
                  onChange={(e) => setSideCamera(e.target.value)}
                >
                  <option value="">None</option>
                  {sideOptions.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </>
            ) : null}
            <button
              type="button"
              onClick={() => void camApi.refreshCameras()}
              className="mt-2 w-full rounded-lg border border-zimon-border py-1.5 text-xs dark:border-cyan-500/20"
            >
              Refresh cameras
            </button>
          </div>

          <div className="rounded-xl border border-zimon-border/70 bg-zimon-card/40 p-3 dark:border-cyan-500/15 dark:bg-slate-950/40">
            <h3 className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted dark:text-cyan-200/55">
              Hardware
            </h3>
            <ul className="space-y-2 text-[11px]">
              {(
                [
                  ['Camera', !!camApi.cam && camApi.previewOn, !!camApi.cam],
                  ['Light', ir.on || white.on || exp.rgbOn, arduinoOk],
                  ['Buzzer', exp.buzz.enabled, arduinoOk],
                  ['Vibration', exp.vib.enabled, arduinoOk],
                  ['Water', water.on, arduinoOk],
                ] as const
              ).map(([label, active, link]) => (
                <li key={label} className="flex items-center justify-between gap-2">
                  <span className="text-zimon-muted">{label}</span>
                  <span className="flex items-center gap-1.5">
                    <span className={`h-2 w-2 rounded-full ${hardwareDot(active, link && !active)}`} />
                    <span className="text-zimon-fg">{active ? 'Active' : link ? 'Standby' : 'N/A'}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        {/* Center */}
        <div className="min-w-0 space-y-3 xl:col-span-6">
          <div className="zimon-camera-frame relative flex min-h-0 flex-col overflow-hidden rounded-2xl">
            <div className="flex shrink-0 items-center justify-between gap-2 border-b border-cyan-500/15 bg-slate-950/95 px-3 py-2 backdrop-blur-md dark:border-cyan-500/20 sm:px-4">
              <div className="flex min-w-0 items-center gap-1.5 text-[10px] font-bold uppercase tracking-[0.14em] text-white/95 sm:text-[11px]">
                <Video className="h-3.5 w-3.5 shrink-0 text-cyan-400" strokeWidth={2.25} />
                <span className="truncate">Live Feed</span>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                {exp.running ? (
                  <span className="flex items-center gap-1 text-[10px] font-bold text-red-400 sm:text-[11px]">
                    <span className="h-2 w-2 animate-pulse rounded-full bg-red-500" />
                    REC
                  </span>
                ) : null}
                {camApi.cam && camApi.previewOn ? (
                  <span className="text-[10px] font-semibold text-emerald-400 sm:text-[11px]">Camera Connected</span>
                ) : camApi.cam ? (
                  <span className="text-[10px] font-semibold text-amber-300 sm:text-[11px]">Standby</span>
                ) : (
                  <span className="text-[10px] font-semibold text-white/50 sm:text-[11px]">No camera</span>
                )}
              </div>
            </div>

            <div
              ref={videoRef}
              className="relative flex min-h-[200px] flex-1 items-center justify-center md:min-h-[280px]"
            >
              {showCameraStream ? (
                <span className="absolute left-3 top-3 z-20 rounded-md border border-cyan-500/25 bg-slate-950/80 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-cyan-200/90 backdrop-blur-sm">
                  {wellSize}-well
                </span>
              ) : null}

              <div className="absolute bottom-3 left-3 z-10 rounded-lg border border-white/10 bg-slate-950/65 px-2.5 py-1 text-[10px] tabular-nums text-white/90 backdrop-blur-md">
                {camApi.meta?.resolution
                  ? `${camApi.meta.resolution[0]} × ${camApi.meta.resolution[1]}`
                  : '— × —'}{' '}
                ·{' '}
                {camApi.meta?.fps != null ? `${Number(camApi.meta.fps).toFixed(0)} FPS` : '— FPS'}
              </div>
              <button
                type="button"
                onClick={() => void toggleFs()}
                className="absolute bottom-3 right-3 z-10 rounded-xl border border-white/10 bg-slate-950/65 p-2 text-white shadow-md backdrop-blur-md transition-colors hover:border-cyan-400/30 hover:bg-slate-900/80"
                title={fs ? 'Exit fullscreen' : 'Fullscreen'}
              >
                {fs ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
              </button>

              {showCameraStream ? (
                <CameraLivePreview
                  active
                  className="max-h-[min(48vh,420px)] w-full object-contain"
                  alt="Camera"
                />
              ) : (
                <div className="flex max-w-lg flex-col items-center gap-4 px-6 py-4">
                  <WellPlateSchematic wells={wellSize} />
                  <span className="text-center text-sm text-white/50">
                    {!camApi.cam ? 'Choose a camera, then enable preview' : 'Enable Camera Preview to stream'}
                  </span>
                </div>
              )}
            </div>

            <CameraPreviewBar
              previewOn={camApi.previewOn}
              hasCamera={!!camApi.cam}
              connectedVisual={!!camApi.cam && camApi.previewOn}
              elapsedRatio={exp.elapsedRatio}
              timerLabel={exp.timerLabel}
              durationS={exp.durationS}
              disabled={!camApi.cam}
              onTogglePreview={() => {
                if (camApi.previewOn) void camApi.stopPreview()
                else void camApi.startPreview()
              }}
              onStopPreview={() => void camApi.stopPreview()}
              onPlayPreview={() => void camApi.startPreview()}
              onBumpDuration={(d) => exp.setDurationS(Math.max(0, exp.durationS + d))}
              className="rounded-none rounded-b-2xl border-0 border-t border-cyan-500/15 bg-slate-950/80 py-2 shadow-none dark:border-cyan-500/18 dark:bg-slate-950/85 dark:shadow-none"
            />
          </div>

          {/* Phase timeline */}
          <div className="rounded-xl border border-cyan-500/15 bg-slate-950/50 p-3 dark:border-cyan-500/20">
            <div className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted">Experiment timeline</div>
            <div className="flex h-10 overflow-hidden rounded-lg border border-white/10">
              {phaseWidths.map((seg, i) => (
                <div
                  key={`${seg.label}-${i}`}
                  style={{ width: `${seg.pct}%` }}
                  className={[
                    'flex items-center justify-center border-r border-white/10 px-1 text-[9px] font-bold uppercase last:border-r-0',
                    seg.kind === 'stimulus'
                      ? 'bg-sky-600/40 text-sky-100'
                      : seg.kind === 'recovery'
                        ? 'bg-violet-600/30 text-violet-100'
                        : 'bg-slate-700/50 text-slate-200',
                  ].join(' ')}
                  title={seg.label}
                >
                  <span className="truncate">{seg.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom info */}
          <div className="grid grid-cols-2 gap-2 rounded-xl border border-zimon-border/60 bg-zimon-card/30 px-3 py-2 text-[10px] dark:border-cyan-500/10 sm:grid-cols-4">
            <div>
              <span className="text-zimon-muted">Duration</span>
              <div className="font-mono text-zimon-fg">{exp.timerLabel}</div>
            </div>
            <div>
              <span className="text-zimon-muted">Clock</span>
              <div className="font-mono text-zimon-fg">{new Date().toLocaleTimeString()}</div>
            </div>
            <div>
              <span className="text-zimon-muted">Phase</span>
              <div className="font-semibold text-cyan-200/90">{ws.currentPhaseLabel}</div>
            </div>
            <div className="col-span-2 min-w-0 sm:col-span-1">
              <span className="text-zimon-muted">Stimuli</span>
              <div className="truncate text-zimon-fg">{exp.activeList}</div>
            </div>
          </div>
        </div>

        {/* Right column */}
        <aside className="space-y-3 xl:col-span-3">
          <div className="rounded-xl border border-zimon-border/70 bg-zimon-card/40 p-3 dark:border-cyan-500/15 dark:bg-slate-950/40">
            <h3 className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted dark:text-cyan-200/55">
              Run
            </h3>
            <div className="flex flex-col gap-2">
              <button
                type="button"
                disabled={exp.running}
                onClick={() => void onStart()}
                className="flex h-10 items-center justify-center gap-2 rounded-xl bg-gradient-to-b from-emerald-500 to-emerald-600 text-sm font-bold text-white shadow-md shadow-emerald-500/25 disabled:opacity-40"
              >
                <Play className="h-4 w-4 fill-current" />
                Start experiment
              </button>
              <button
                type="button"
                onClick={() => void onStop()}
                className="flex h-10 items-center justify-center gap-2 rounded-xl border border-red-500/40 bg-gradient-to-b from-red-950/90 to-red-900 text-sm font-bold text-red-100"
              >
                <Square className="h-3.5 w-3.5 fill-current" />
                Stop
              </button>
              <button
                type="button"
                disabled
                title="Pause is not supported by the experiment runner"
                className="flex h-9 cursor-not-allowed items-center justify-center gap-2 rounded-xl border border-white/10 text-xs text-zimon-muted opacity-50"
              >
                <Pause className="h-3.5 w-3.5" />
                Pause
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-zimon-border/70 bg-zimon-card/40 p-3 dark:border-cyan-500/15 dark:bg-slate-950/40">
            <h3 className="mb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted dark:text-cyan-200/55">
              Manual test
            </h3>
            <div className="space-y-2 text-xs">
              <button
                type="button"
                disabled={!arduinoOk}
                onClick={() => {
                  const on = !ir.on
                  applyIr({ on, v: ir.v })
                  ws.appendActionLog(`Manual IR ${on ? 'ON' : 'OFF'}`)
                }}
                className="w-full rounded-lg border border-zimon-border py-2 dark:border-cyan-500/20"
              >
                Light (IR) toggle
              </button>
              <button
                type="button"
                disabled={!arduinoOk}
                onClick={() => {
                  const on = !exp.buzz.enabled
                  const inten = on && exp.buzz.intensity < 5 ? 55 : exp.buzz.intensity
                  exp.setBuzzP({ enabled: on, intensity: inten })
                  exp.sendBuzz(on ? mapToPwm(inten) : 0)
                  ws.appendActionLog(`Manual Buzzer ${on ? 'ON' : 'OFF'}`)
                }}
                className="w-full rounded-lg border border-zimon-border py-2 dark:border-cyan-500/20"
              >
                Buzzer toggle
              </button>
              <button
                type="button"
                disabled={!arduinoOk}
                onClick={() => {
                  const on = !exp.vib.enabled
                  const inten = on && exp.vib.intensity < 5 ? 50 : exp.vib.intensity
                  exp.setVibP({ enabled: on, intensity: inten })
                  exp.sendVib(on ? mapToPwm(inten) : 0)
                  ws.appendActionLog(`Manual Vibration ${on ? 'ON' : 'OFF'}`)
                }}
                className="w-full rounded-lg border border-zimon-border py-2 dark:border-cyan-500/20"
              >
                Vibration toggle
              </button>
              <button
                type="button"
                disabled={!arduinoOk}
                onClick={() => {
                  applyWater({ on: !water.on, v: water.v })
                  ws.appendActionLog(`Manual Water ${!water.on ? 'ON' : 'OFF'}`)
                }}
                className="w-full rounded-lg border border-zimon-border py-2 dark:border-cyan-500/20"
              >
                Water toggle
              </button>
            </div>
          </div>
        </aside>
      </div>

      {/* Control deck */}
      <div className="zimon-control-deck rounded-xl border border-cyan-500/10 px-3 py-2.5 md:px-4 md:py-3 dark:border-cyan-500/15">
        <h2 className="mb-2 border-b border-cyan-500/10 pb-1.5 text-center text-[10px] font-bold uppercase tracking-[0.28em] text-zimon-muted dark:text-cyan-200/65">
          Controls
        </h2>

        <div className="flex flex-col gap-3 lg:flex-row lg:items-stretch lg:gap-0">
          <div className={`flex shrink-0 justify-center lg:pr-3 ${isLarval ? 'lg:w-[140px]' : 'lg:w-[168px]'}`}>
            <FpsGaugePanel
              compact
              fps={camApi.fps}
              onBump={(d) => camApi.bumpFps(d)}
              onApply={() => void camApi.applyFps()}
              disabled={!camApi.cam}
            />
          </div>

          <div
            className="hidden shrink-0 self-stretch lg:block lg:w-px lg:bg-gradient-to-b lg:from-transparent lg:via-cyan-500/15 lg:to-transparent"
            aria-hidden
          />

          <div className="min-w-0 flex-1 lg:px-4">
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                disabled={exp.running}
                onClick={() => void onStart()}
                className="zimon-btn-primary-glow flex h-9 items-center justify-center gap-1.5 rounded-xl bg-gradient-to-b from-emerald-500 to-emerald-600 text-xs font-bold text-white shadow-md shadow-emerald-500/25 ring-1 ring-emerald-400/35 hover:from-emerald-400 hover:to-emerald-600 disabled:opacity-40"
              >
                <Play className="h-3.5 w-3.5 fill-current" />
                Start
              </button>
              <button
                type="button"
                onClick={() => void onStop()}
                className="zimon-btn-danger-glow flex h-9 items-center justify-center gap-1.5 rounded-xl border border-red-500/40 bg-gradient-to-b from-red-950/90 to-red-900 text-xs font-bold text-red-100 shadow-md shadow-red-500/15 ring-1 ring-red-500/25 hover:border-red-400/60"
              >
                <Square className="h-3 w-3 fill-current" />
                Stop
              </button>
            </div>
            <div className="mt-1.5 flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-[9px] text-zimon-muted">
              <label className="inline-flex items-center gap-1.5">
                <span className="whitespace-nowrap">Rec. cap (s)</span>
                <input
                  type="number"
                  min={0}
                  className="w-14 rounded-md border border-zimon-border bg-slate-900/50 px-1.5 py-0.5 text-[10px] text-zimon-fg focus:border-cyan-400/50 focus:outline-none focus:ring-1 focus:ring-cyan-400/20 dark:border-cyan-500/20"
                  value={exp.durationS}
                  onChange={(e) => exp.setDurationS(Number(e.target.value))}
                />
              </label>
              <span
                className="hidden rounded-full border border-cyan-500/15 bg-cyan-500/10 px-2 py-0.5 font-semibold text-cyan-800 sm:inline dark:text-cyan-300/90"
                title="Lighting summary"
              >
                {lightingPill}
              </span>
            </div>
            <div className={`mt-2 grid grid-cols-1 gap-1.5 ${isLarval ? 'sm:grid-cols-2' : 'sm:grid-cols-3'}`}>
              <LightingToggleCard
                compact
                title="IR Light"
                spec="880 nm"
                icon={<Waves className="h-3.5 w-3.5 text-red-400" strokeWidth={2.2} />}
                active={ir.on}
                intensity={ir.v}
                connected={arduinoOk}
                accent="ir"
                onToggle={(on) => {
                  applyIr({ on, v: ir.v })
                  ws.appendActionLog(`IR ${on ? 'ON' : 'OFF'}`)
                }}
                onIntensity={(v) => applyIr({ on: true, v })}
              />
              <LightingToggleCard
                compact
                title="White Light"
                spec="5500 K"
                icon={<SunMedium className="h-3.5 w-3.5 text-amber-400" strokeWidth={2.2} />}
                active={white.on}
                intensity={white.v}
                connected={arduinoOk}
                accent="white"
                onToggle={(on) => {
                  applyWhite({ on, v: white.v })
                  ws.appendActionLog(`White ${on ? 'ON' : 'OFF'}`)
                }}
                onIntensity={(v) => applyWhite({ on: true, v })}
              />
              {!isLarval ? (
                <LightingToggleCard
                  compact
                  title="RGB Light"
                  spec="Spectrum"
                  icon={<Palette className="h-3.5 w-3.5 text-violet-400" strokeWidth={2.2} />}
                  active={exp.rgbOn}
                  intensity={exp.rgbIntensityPct}
                  connected={arduinoOk}
                  accent="rgb"
                  onToggle={(on) => {
                    exp.setRgbOn(on)
                    ws.appendActionLog(`RGB ${on ? 'ON' : 'OFF'}`)
                  }}
                  onIntensity={(v) => exp.setRgbIntensityPct(v)}
                  colorExtra={
                    <div className="flex items-center justify-end gap-1">
                      <span
                        className="h-3 w-3 shrink-0 rounded-sm border border-white/15 shadow-inner"
                        style={{ backgroundColor: exp.rgbHex }}
                        aria-hidden
                      />
                      <input
                        type="color"
                        value={exp.rgbHex}
                        onChange={(e) => exp.setRgbHex(e.target.value)}
                        disabled={!exp.rgbOn}
                        title="RGB color"
                        className="h-5 w-8 cursor-pointer overflow-hidden rounded border-0 bg-transparent p-0 disabled:opacity-40"
                      />
                    </div>
                  }
                />
              ) : null}
            </div>
          </div>

          <div
            className="hidden shrink-0 self-stretch lg:block lg:w-px lg:bg-gradient-to-b lg:from-transparent lg:via-cyan-500/15 lg:to-transparent"
            aria-hidden
          />

          <div className={`flex w-full shrink-0 flex-col gap-1.5 lg:pl-3 ${isLarval ? 'lg:w-[180px]' : 'lg:w-[200px] xl:w-[220px]'}`}>
            <h3 className="text-[9px] font-bold uppercase tracking-[0.18em] text-zimon-muted dark:text-cyan-200/50">
              Auxiliary
            </h3>
            <AuxiliarySwitchRow
              compact
              icon={<span className="text-sm leading-none">🔊</span>}
              label="Buzzer"
              checked={exp.buzz.enabled}
              disabled={!arduinoOk}
              onChange={(on) => {
                const inten = on && exp.buzz.intensity < 5 ? 55 : exp.buzz.intensity
                exp.setBuzzP({ enabled: on, intensity: inten })
                exp.sendBuzz(on ? mapToPwm(inten) : 0)
                ws.appendActionLog(`Buzzer ${on ? 'ON' : 'OFF'}`)
              }}
            />
            <AuxiliarySwitchRow
              compact
              icon={<span className="text-sm leading-none">〰</span>}
              label="Vibration"
              checked={exp.vib.enabled}
              disabled={!arduinoOk}
              onChange={(on) => {
                const inten = on && exp.vib.intensity < 5 ? 50 : exp.vib.intensity
                exp.setVibP({ enabled: on, intensity: inten })
                exp.sendVib(on ? mapToPwm(inten) : 0)
                ws.appendActionLog(`Vibration ${on ? 'ON' : 'OFF'}`)
              }}
            />
            <AuxiliarySwitchRow
              compact
              icon={<span className="text-sm leading-none">≋</span>}
              label="Water circulation"
              checked={water.on}
              disabled={!arduinoOk}
              onChange={(on) => {
                applyWater({ on, v: water.v })
                ws.appendActionLog(`Water ${on ? 'ON' : 'OFF'}`)
              }}
            />
            {water.on ? (
              <div className="px-0.5 pt-0.5" onClick={(e) => e.stopPropagation()}>
                <input
                  type="range"
                  min={5}
                  max={100}
                  value={water.v}
                  disabled={!arduinoOk}
                  onChange={(e) => applyWater({ on: true, v: Number(e.target.value) })}
                  className="h-1.5 w-full accent-cyan-500 dark:accent-cyan-400"
                />
                <div className="text-center text-[8px] text-zimon-muted">Pump {water.v}%</div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* Event log (larval emphasis + always visible strip) */}
      <div className="rounded-xl border border-zimon-border/60 bg-slate-950/40 p-3 dark:border-cyan-500/10">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted">Stimulus / event log</h3>
          <button type="button" onClick={ws.clearActionLog} className="text-[10px] text-cyan-400 hover:underline">
            Clear
          </button>
        </div>
        <ul
          className={`max-h-28 space-y-1 overflow-y-auto font-mono text-[10px] text-slate-300 ${isLarval ? 'max-h-40' : ''}`}
        >
          {ws.actionLog.length === 0 ? (
            <li className="text-zimon-muted">No events yet.</li>
          ) : (
            ws.actionLog.map((line, i) => (
              <li key={`${i}-${line.slice(0, 12)}`}>{line}</li>
            ))
          )}
        </ul>
      </div>
    </div>
  )
}
