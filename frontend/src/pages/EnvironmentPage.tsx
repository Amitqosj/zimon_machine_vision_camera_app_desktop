import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CameraLivePreview } from '../components/CameraLivePreview'
import { apiFetch } from '../api/client'
import { ReadinessDashboard } from '../features/environment/ReadinessDashboard'
import { mapToPwm } from '../utils/pwm'

type CamList = { cameras: string[] }
type CamMeta = {
  type: string
  fps: number | null
  resolution: [number, number] | null
  zoom: number | null
}
type ResList = { resolutions: { width: number; height: number }[] }
type TempRes = { celsius: number | null }
type PreviewStatus = { previewing: string[] }

const RES_PRESETS = [
  '640x480',
  '800x600',
  '1024x768',
  '1280x720',
  '1280x1024',
  '1920x1080',
  '2048x1536',
]

function EnvSliderRow({
  label,
  connected,
  onSend,
}: {
  label: string
  connected: boolean
  onSend: (pwm: number) => void
}) {
  const [enabled, setEnabled] = useState(false)
  const [v, setV] = useState(0)

  const apply = useCallback(
    (nextEn: boolean, nextV: number) => {
      if (!connected) return
      onSend(nextEn ? mapToPwm(nextV) : 0)
    },
    [connected, onSend],
  )

  return (
    <div className="flex flex-wrap items-center gap-3 py-1">
      <span className="text-sm text-gray-300 w-24 shrink-0">{label}</span>
      <label className="flex items-center gap-2 text-xs text-gray-500">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => {
            const en = e.target.checked
            setEnabled(en)
            if (!en) setV(0)
            apply(en, en ? v : 0)
          }}
        />
        Enable
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
        className="flex-1 min-w-[120px] accent-indigo-500"
      />
      <span className="text-xs font-mono text-gray-500 w-8">{v}</span>
    </div>
  )
}

export function EnvironmentPage() {
  const [cameras, setCameras] = useState<string[]>([])
  const [cam, setCam] = useState('')
  const [previewOn, setPreviewOn] = useState(false)
  const [meta, setMeta] = useState<CamMeta | null>(null)
  const [supportedRes, setSupportedRes] = useState<{ width: number; height: number }[]>([])
  const [fps, setFps] = useState(60)
  const [zoomPct, setZoomPct] = useState(100)
  const [resolutionPick, setResolutionPick] = useState('1280x720')
  const [temp, setTemp] = useState<number | null>(null)
  const [arduinoOk, setArduinoOk] = useState(false)
  const [err, setErr] = useState('')

  const refreshCameras = useCallback(async () => {
    try {
      await apiFetch('/api/camera/refresh', { method: 'POST' })
      const r = await apiFetch<CamList>('/api/camera/list')
      setCameras(r.cameras)
      setCam((prev) =>
        prev && r.cameras.includes(prev) ? prev : r.cameras[0] || '',
      )
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }, [])

  const pollArduino = useCallback(async () => {
    try {
      const s = await apiFetch<{ connected: boolean }>('/api/arduino/status')
      setArduinoOk(s.connected)
    } catch {
      setArduinoOk(false)
    }
  }, [])

  useEffect(() => {
    void refreshCameras()
    void pollArduino()
    const id = window.setInterval(() => void pollArduino(), 3000)
    return () => window.clearInterval(id)
  }, [refreshCameras, pollArduino])

  useEffect(() => {
    let cancelled = false
    const syncPreview = async () => {
      try {
        const r = await apiFetch<PreviewStatus>('/api/camera/preview/status')
        if (cancelled) return
        if (!cam) {
          setPreviewOn(false)
          return
        }
        setPreviewOn(r.previewing.includes(cam))
      } catch {
        /* keep last state on transient errors */
      }
    }
    void syncPreview()
    const id = window.setInterval(() => void syncPreview(), 2500)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [cam])

  useEffect(() => {
    if (!cam) return
    const load = async () => {
      try {
        const m = await apiFetch<CamMeta>(
          `/api/camera/meta?camera_name=${encodeURIComponent(cam)}`,
        )
        setMeta(m)
        if (m.zoom != null) setZoomPct(Math.round(m.zoom * 100))
        if (m.resolution) {
          const [w, h] = m.resolution
          setResolutionPick(`${w}x${h}`)
        }
      } catch {
        setMeta(null)
      }
      try {
        const sr = await apiFetch<ResList>(
          `/api/camera/supported-resolutions?camera_name=${encodeURIComponent(cam)}`,
        )
        setSupportedRes(sr.resolutions || [])
      } catch {
        setSupportedRes([])
      }
    }
    void load()
  }, [cam, previewOn])

  useEffect(() => {
    if (!arduinoOk) {
      setTemp(null)
      return
    }
    const id = window.setInterval(async () => {
      try {
        const t = await apiFetch<TempRes>('/api/arduino/temperature')
        setTemp(t.celsius)
      } catch {
        setTemp(null)
      }
    }, 3000)
    return () => window.clearInterval(id)
  }, [arduinoOk])

  async function applyFps() {
    if (!cam) return
    setErr('')
    try {
      await apiFetch(
        `/api/camera/settings?camera_name=${encodeURIComponent(cam)}`,
        {
          method: 'POST',
          body: JSON.stringify({ setting: 'fps', value: fps }),
        },
      )
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function applyZoom() {
    if (!cam) return
    setErr('')
    try {
      await apiFetch(
        `/api/camera/settings?camera_name=${encodeURIComponent(cam)}`,
        {
          method: 'POST',
          body: JSON.stringify({ setting: 'zoom', value: zoomPct / 100 }),
        },
      )
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function applyResolution() {
    if (!cam) return
    const [w, h] = resolutionPick.split('x').map(Number)
    if (!w || !h) return
    setErr('')
    try {
      await apiFetch(
        `/api/camera/settings?camera_name=${encodeURIComponent(cam)}`,
        {
          method: 'POST',
          body: JSON.stringify({ setting: 'resolution', value: [w, h] }),
        },
      )
      if (previewOn) {
        await apiFetch(
          `/api/camera/preview/stop?camera_name=${encodeURIComponent(cam)}`,
          { method: 'POST' },
        )
        await apiFetch(
          `/api/camera/preview/start?camera_name=${encodeURIComponent(cam)}`,
          { method: 'POST' },
        )
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function startPreview() {
    if (!cam) return
    setErr('')
    try {
      await apiFetch(
        `/api/camera/preview/start?camera_name=${encodeURIComponent(cam)}`,
        { method: 'POST' },
      )
      setPreviewOn(true)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function stopPreview() {
    if (!cam) return
    try {
      await apiFetch(
        `/api/camera/preview/stop?camera_name=${encodeURIComponent(cam)}`,
        { method: 'POST' },
      )
    } finally {
      setPreviewOn(false)
    }
  }

  const sendCmd = async (cmd: string) => {
    try {
      await apiFetch('/api/arduino/command', {
        method: 'POST',
        body: JSON.stringify({ command: cmd }),
      })
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-4 pb-8">
      <ReadinessDashboard />
      <div className="flex items-center justify-end">
        <Link
          to="/app/calibration"
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
        >
          Calibration
        </Link>
      </div>
      <details className="rounded-xl border border-zimon-border/70 bg-zimon-card/30 open:pb-2 dark:border-cyan-500/15 dark:bg-slate-950/25">
        <summary className="cursor-pointer select-none px-4 py-3 text-sm font-semibold text-cyan-200/90 hover:bg-slate-900/40">
          Advanced camera &amp; environment
        </summary>
        <div className="border-t border-zimon-border/50 px-2 pb-4 pt-4 dark:border-cyan-500/10 md:px-0">
      <p className="text-[11px] leading-relaxed text-gray-500 border border-zimon-border/80 rounded-lg bg-zimon-card/40 px-3 py-2">
        This screen talks to the{' '}
        <span className="text-gray-400">FastAPI</span> process (same Arduino/camera stack as the desktop app when you
        run <span className="font-mono text-gray-400">uvicorn backend.api.main:app</span>). Only one app can hold the
        serial port — quit PyQt or disconnect there before connecting here.
      </p>
      {!arduinoOk ? (
        <p className="text-xs text-amber-400/90 bg-amber-500/10 border border-amber-500/25 rounded-lg px-3 py-2">
          Arduino not connected. Open{' '}
          <Link to="/app/settings" className="underline text-indigo-300">
            Settings
          </Link>{' '}
          to choose a serial port and connect (same as the desktop app).
        </p>
      ) : null}

      {err ? (
        <div className="rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm px-3 py-2">
          {err}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        <section className="lg:col-span-3 rounded-2xl border border-zimon-border bg-zimon-panel p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-400">Camera Preview</h2>
          <div className="flex flex-wrap gap-2 items-center">
            <span className="text-sm text-gray-400">Camera:</span>
            <select
              className="flex-1 min-w-[200px] rounded-lg bg-zimon-card border border-zimon-border px-2 py-2 text-sm"
              value={cam}
              onChange={(e) => setCam(e.target.value)}
            >
              {cameras.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => void refreshCameras()}
              className="rounded-lg border border-zimon-border px-3 py-2 text-sm"
              title="Refresh camera list"
            >
              🔄
            </button>
            {!previewOn ? (
              <button
                type="button"
                onClick={() => void startPreview()}
                className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white"
              >
                Start preview
              </button>
            ) : (
              <button
                type="button"
                onClick={() => void stopPreview()}
                className="rounded-lg border border-red-500/40 px-3 py-2 text-sm text-red-300"
              >
                Stop
              </button>
            )}
          </div>
          <div
            className="rounded-xl overflow-hidden bg-[#0d0f13] border border-zimon-border flex items-center justify-center min-h-[250px] max-h-[450px]"
          >
            {previewOn && cam ? (
              <CameraLivePreview
                active
                className="max-h-[450px] w-full object-contain"
                alt="Camera preview"
              />
            ) : (
              <span className="text-gray-600 text-sm">
                {!cam ? 'No camera selected' : 'Start preview to see the stream'}
              </span>
            )}
          </div>
          {meta?.fps != null && previewOn ? (
            <div className="text-right text-xs text-cyan-400 font-bold">
              FPS: {typeof meta.fps === 'number' ? meta.fps.toFixed(1) : meta.fps}
            </div>
          ) : null}
        </section>

        <section className="lg:col-span-2 rounded-2xl border border-zimon-border bg-zimon-panel p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-400">Camera Settings</h2>
          <div className="flex items-center gap-2 text-sm">
            <span
              className={
                !cam ? 'text-gray-500' : previewOn ? 'text-cyan-400' : 'text-amber-500/90'
              }
            >
              ●
            </span>
            <span>
              {!cam
                ? 'No camera selected'
                : previewOn
                  ? 'Preview running'
                  : 'Not streaming'}
            </span>
          </div>
          <div className="h-px bg-zimon-border" />
          <div className="text-xs space-y-1 text-gray-300">
            <div>FPS: {meta?.fps != null ? `${Number(meta.fps).toFixed(1)}` : '—'}</div>
            <div>
              Resolution:{' '}
              {meta?.resolution
                ? `${meta.resolution[0]}×${meta.resolution[1]}`
                : '—'}
            </div>
            <div>Zoom: {meta?.zoom != null ? `${meta.zoom.toFixed(1)}x` : '—'}</div>
          </div>
          <div className="h-px bg-zimon-border" />
          <p className="text-xs text-gray-500 font-medium">Controls</p>
          <div className="flex items-center gap-2 text-sm">
            <span className="w-12">FPS</span>
            <input
              type="number"
              min={1}
              max={120}
              className="w-20 rounded bg-zimon-card border border-zimon-border px-2 py-1"
              value={fps}
              onChange={(e) => setFps(Number(e.target.value))}
            />
            <button
              type="button"
              onClick={() => void applyFps()}
              className="text-xs text-indigo-400 hover:underline"
            >
              Apply
            </button>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <span className="w-12">Zoom</span>
            <input
              type="range"
              min={50}
              max={200}
              value={zoomPct}
              onChange={(e) => setZoomPct(Number(e.target.value))}
              className="flex-1 accent-indigo-500"
            />
            <span className="text-xs w-10">{(zoomPct / 100).toFixed(1)}x</span>
            <button
              type="button"
              onClick={() => void applyZoom()}
              className="text-xs text-indigo-400 hover:underline"
            >
              Apply
            </button>
          </div>
          <div className="flex flex-col gap-1 text-sm">
            <span>Resolution</span>
            <select
              className="rounded-lg bg-zimon-card border border-zimon-border px-2 py-2 text-sm"
              value={resolutionPick}
              onChange={(e) => setResolutionPick(e.target.value)}
            >
              {supportedRes.length > 0
                ? supportedRes.map((r) => (
                    <option key={`${r.width}x${r.height}`} value={`${r.width}x${r.height}`}>
                      {r.width}×{r.height}
                    </option>
                  ))
                : RES_PRESETS.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
            </select>
            <button
              type="button"
              onClick={() => void applyResolution()}
              className="mt-1 rounded-lg bg-indigo-600/80 py-1.5 text-xs font-semibold text-white"
            >
              Apply resolution
            </button>
          </div>
        </section>
      </div>

      <section className="rounded-2xl border border-zimon-border bg-zimon-panel p-5 space-y-3">
        <h2 className="text-sm font-semibold text-gray-400">Environment Variables</h2>
        <p className="text-xs text-gray-500">
          Control environmental conditions for consistent experiments.
        </p>
        <EnvSliderRow
          label="IR Light"
          connected={arduinoOk}
          onSend={(pwm) => void sendCmd(`IR ${pwm}`)}
        />
        <EnvSliderRow
          label="White Light"
          connected={arduinoOk}
          onSend={(pwm) => void sendCmd(`WHITE ${pwm}`)}
        />
        <EnvSliderRow
          label="Pump"
          connected={arduinoOk}
          onSend={(pwm) => void sendCmd(`PUMP ${pwm}`)}
        />
        <div className="h-px bg-zimon-border my-2" />
        <div className="flex items-center gap-2 text-sm">
          <span>🌡</span>
          <span className="text-gray-300">Temperature:</span>
          <span className="text-white font-medium">
            {temp != null ? `${temp.toFixed(1)} °C` : '-- °C'}
          </span>
        </div>
      </section>
        </div>
      </details>
    </div>
  )
}
