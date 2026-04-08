import { FolderOpen } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client'

type Status = { connected: boolean; port: string | null }
type Ports = { ports: string[] }
type ZzStatus = { configured_path: string; available: boolean; resolved_exe: string | null }

function SettingsCard({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="relative rounded-xl border border-zimon-border bg-[#14161a] shadow-[0_8px_32px_rgba(0,0,0,0.35)]">
      <div className="absolute -top-3 left-5 z-[1] border border-zimon-border bg-[#14161a] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-gray-400">
        {title}
      </div>
      <div className="space-y-4 p-5 pt-7">{children}</div>
    </section>
  )
}

function FieldRow({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
      <span className="w-full shrink-0 text-sm font-medium text-gray-400 sm:w-36">{label}</span>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  )
}

function fileWithPath(file: File): string | null {
  const p = (file as File & { path?: string }).path
  return typeof p === 'string' && p.length > 0 ? p : null
}

export function SettingsPage() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [ports, setPorts] = useState<string[]>([])
  const [port, setPort] = useState('')
  const [arduino, setArduino] = useState<Status | null>(null)
  const [zzPath, setZzPath] = useState('')
  const [zzStatus, setZzStatus] = useState<ZzStatus | null>(null)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [browseBusy, setBrowseBusy] = useState(false)

  const refreshPorts = useCallback(async () => {
    try {
      const r = await apiFetch<Ports>('/api/arduino/ports')
      setPorts(r.ports)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }, [])

  const refreshArduino = useCallback(async () => {
    try {
      const r = await apiFetch<Status>('/api/arduino/status')
      setArduino(r)
      if (r.port && ports.includes(r.port)) setPort(r.port)
    } catch {
      setArduino(null)
    }
  }, [ports])

  const loadSettings = useCallback(async () => {
    try {
      const s = await apiFetch<{ zebrazoom_exe: string }>('/api/settings')
      setZzPath(s.zebrazoom_exe || '')
    } catch {
      /* ignore */
    }
    try {
      const z = await apiFetch<ZzStatus>('/api/settings/zebrazoom/status')
      setZzStatus(z)
    } catch {
      setZzStatus(null)
    }
  }, [])

  useEffect(() => {
    void refreshPorts()
    void loadSettings()
  }, [refreshPorts, loadSettings])

  useEffect(() => {
    void refreshArduino()
  }, [refreshArduino])

  async function connect() {
    setErr('')
    setMsg('')
    const p = port || ports[0]
    if (!p) {
      setErr('No serial port selected')
      return
    }
    try {
      await apiFetch('/api/arduino/connect', {
        method: 'POST',
        body: JSON.stringify({ port: p }),
      })
      setMsg(`Connected to ${p}`)
      await refreshArduino()
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function autoConnect() {
    setErr('')
    setMsg('')
    try {
      const r = await apiFetch<{ ok: boolean; port: string | null }>(
        '/api/arduino/auto-connect',
        { method: 'POST' },
      )
      if (r.ok && r.port) {
        setPort(r.port)
        setMsg(`Auto-connected on ${r.port}`)
      } else {
        setErr('Auto-connect did not find a usable port')
      }
      await refreshPorts()
      await refreshArduino()
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function disconnect() {
    setErr('')
    setMsg('')
    try {
      await apiFetch('/api/arduino/disconnect', { method: 'POST' })
      setMsg('Arduino disconnected')
      await refreshArduino()
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function testArduino() {
    setErr('')
    setMsg('')
    try {
      const r = await apiFetch<{ reply: string | null }>('/api/arduino/command', {
        method: 'POST',
        body: JSON.stringify({ command: 'STATUS' }),
      })
      if (r.reply) setMsg(`Arduino: ${r.reply}`)
      else setErr('No reply to STATUS')
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function saveZebraZoom() {
    setErr('')
    setMsg('')
    try {
      await apiFetch('/api/settings', {
        method: 'PUT',
        body: JSON.stringify({ zebrazoom_exe: zzPath }),
      })
      setMsg('ZebraZoom path saved')
      await loadSettings()
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function testZebraZoom() {
    setErr('')
    setMsg('')
    if (!zzPath.trim()) {
      setErr('Enter path to ZebraZoom.exe first')
      return
    }
    try {
      await apiFetch('/api/settings', {
        method: 'PUT',
        body: JSON.stringify({ zebrazoom_exe: zzPath.trim() }),
      })
      const t = await apiFetch<{ ok: boolean; message: string }>(
        '/api/settings/zebrazoom/test',
        {
          method: 'POST',
          body: JSON.stringify({ path: zzPath.trim() }),
        },
      )
      setMsg(t.message || (t.ok ? 'OK' : 'Check path'))
      await loadSettings()
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function browseZebraZoom() {
    setErr('')
    setMsg('')
    setBrowseBusy(true)
    try {
      const r = await apiFetch<{ path: string }>('/api/settings/zebrazoom/browse', {
        method: 'POST',
      })
      if (r.path) {
        setZzPath(r.path)
        setMsg('Path selected (system file dialog).')
        return
      }
      setMsg('No file chosen. Paste the path manually or click Browse again.')
      return
    } catch {
      /* API unreachable or native dialog unavailable — browser file picker as fallback */
      fileInputRef.current?.click()
    } finally {
      setBrowseBusy(false)
    }
  }

  function onZebraZoomFilePicked(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    e.target.value = ''
    if (!f) return
    const p = fileWithPath(f)
    if (p) {
      setZzPath(p)
      setMsg('Path selected.')
      return
    }
    setMsg(
      `Selected “${f.name}”. Paste the full path from File Explorer into the field (standard browsers hide disk paths).`,
    )
  }

  const connected = arduino?.connected ?? false

  return (
    <div className="mx-auto w-full max-w-2xl space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="border-l-4 border-zimon-accent bg-indigo-500/10 py-1 pl-3 text-xl font-bold text-white">
            Settings
          </h1>
          <p className="mt-2 text-xs text-gray-500">
            Arduino serial link and ZebraZoom executable — same layout as the desktop app.
          </p>
        </div>
        <Link to="/app/adult" className="text-sm text-zimon-muted hover:text-zimon-fg">
          Back to Home
        </Link>
      </div>

      {err ? (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {err}
        </div>
      ) : null}
      {msg ? (
        <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
          {msg}
        </div>
      ) : null}

      <SettingsCard title="Arduino Settings">
        <FieldRow label="Connection status:">
          <span className={`text-sm font-semibold ${connected ? 'text-sky-400' : 'text-red-400'}`}>
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </FieldRow>

        <FieldRow label="Serial port:">
          <div className="flex flex-wrap items-stretch gap-2">
            <select
              className="min-w-[12rem] flex-1 rounded-lg border border-zimon-border bg-zimon-card px-3 py-2.5 text-sm text-gray-100 outline-none focus:border-indigo-500/60"
              value={port}
              onChange={(e) => setPort(e.target.value)}
            >
              <option value="">Select…</option>
              {ports.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
            <button
              type="button"
              onClick={() => void refreshPorts()}
              className="shrink-0 rounded-lg border border-zimon-border px-4 py-2.5 text-sm font-medium text-gray-200 transition hover:border-gray-500 hover:bg-white/5"
            >
              Refresh
            </button>
          </div>
        </FieldRow>

        <div className="flex flex-wrap gap-2 border-t border-zimon-border pt-4">
          <button
            type="button"
            onClick={() => void connect()}
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-900/30 transition hover:bg-indigo-500"
          >
            Connect
          </button>
          <button
            type="button"
            onClick={() => void autoConnect()}
            className="rounded-lg border border-indigo-500/50 px-5 py-2.5 text-sm font-medium text-indigo-200 transition hover:bg-indigo-500/10"
            title="Try ArduinoController.auto_connect() on the API host"
          >
            Auto-connect
          </button>
          <button
            type="button"
            onClick={() => void disconnect()}
            className="rounded-lg border border-zimon-border px-5 py-2.5 text-sm font-medium text-gray-200 transition hover:bg-white/5"
          >
            Disconnect
          </button>
          <button
            type="button"
            onClick={() => void testArduino()}
            className="ml-auto rounded-lg border border-indigo-500/40 px-5 py-2.5 text-sm font-medium text-indigo-200 transition hover:bg-indigo-500/10"
          >
            Test connection
          </button>
        </div>

        <FieldRow label="Current port:">
          <span className="text-sm text-gray-300">{arduino?.port || 'None'}</span>
        </FieldRow>
      </SettingsCard>

      <SettingsCard title="ZebraZoom Settings">
        <p className="text-[11px] leading-relaxed text-gray-500">
          Specify the path to <span className="text-gray-400">ZebraZoom.exe</span> (the file, not the folder) — used
          by Analysis.
        </p>

        <FieldRow label="Status:">
          <span
            className={`text-sm font-semibold ${zzStatus?.available ? 'text-sky-400' : 'text-amber-400'}`}
          >
            {zzStatus?.available ? 'Available' : 'Not available'}
          </span>
        </FieldRow>

        {zzStatus?.resolved_exe ? (
          <FieldRow label="Resolved:">
            <span className="break-all font-mono text-xs text-gray-400">{zzStatus.resolved_exe}</span>
          </FieldRow>
        ) : null}

        <FieldRow label="ZebraZoom.exe:">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-stretch">
            <input
              className="min-w-0 flex-1 rounded-lg border border-zimon-border bg-zimon-card px-3 py-2.5 font-mono text-sm text-gray-100 outline-none placeholder:text-gray-600 focus:border-indigo-500/60"
              placeholder="C:\path\to\ZebraZoom.exe"
              value={zzPath}
              onChange={(e) => setZzPath(e.target.value)}
            />
            <button
              type="button"
              disabled={browseBusy}
              onClick={() => void browseZebraZoom()}
              className="inline-flex shrink-0 items-center justify-center gap-2 rounded-lg border border-zimon-border bg-zimon-card px-4 py-2.5 text-sm font-semibold text-gray-100 transition hover:border-indigo-500/50 hover:bg-white/5 disabled:opacity-50"
            >
              <FolderOpen className="h-4 w-4 text-indigo-400" aria-hidden />
              {browseBusy ? 'Opening…' : 'Browse'}
            </button>
          </div>
        </FieldRow>

        <input
          ref={fileInputRef}
          type="file"
          accept=".exe,application/x-msdownload"
          className="sr-only"
          tabIndex={-1}
          aria-hidden
          onChange={onZebraZoomFilePicked}
        />

        <p className="text-[10px] leading-relaxed text-gray-600">
          <strong className="text-gray-500">Browse</strong> opens a file dialog on the PC running the ZIMON API (same
          machine as the PyQt / lab app when the API is local).{' '}
          <button
            type="button"
            className="font-semibold text-indigo-400 underline-offset-2 hover:underline"
            onClick={() => fileInputRef.current?.click()}
          >
            Use browser file picker
          </button>{' '}
          if the server dialog does not appear; standard browsers may only expose the file name — paste the full path
          from Explorer if needed.
        </p>

        <div className="flex flex-wrap gap-2 border-t border-zimon-border pt-4">
          <button
            type="button"
            onClick={() => void saveZebraZoom()}
            className="rounded-lg border border-zimon-border px-5 py-2.5 text-sm font-medium text-gray-200 transition hover:bg-white/5"
          >
            Save path
          </button>
          <button
            type="button"
            onClick={() => void testZebraZoom()}
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-900/30 transition hover:bg-indigo-500"
          >
            Test &amp; save
          </button>
        </div>
      </SettingsCard>
    </div>
  )
}
