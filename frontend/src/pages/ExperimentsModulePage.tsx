import { Copy, Play, SkipBack, Square } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch, recordingsMediaUrl } from '../api/client'
import { useHardwareStatus } from '../context/HardwareStatusContext'
import { useZimonWorkspace } from '../context/ZimonWorkspaceContext'
import type { StimulusType } from '../types/zimonProtocol'

type RecordingItem = {
  relpath: string
  full_path?: string
  name: string
  size: number
  modified_iso: string
}

type ListOut = { root: string; items: RecordingItem[] }

type DateFilter = 'all' | '24h' | '7d' | '30d'

function inDateRange(iso: string, f: DateFilter): boolean {
  if (f === 'all') return true
  const t = new Date(iso).getTime()
  if (Number.isNaN(t)) return true
  const now = Date.now()
  const ms = f === '24h' ? 864e5 : f === '7d' ? 7 * 864e5 : 30 * 864e5
  return now - t <= ms
}

function experimentIdFromFile(name: string): string {
  const base = name.replace(/\.[^.]+$/, '')
  const safe = base.replace(/[^a-zA-Z0-9_-]+/g, '_').slice(0, 32)
  return `EXP_${safe || 'FILE'}`
}

export function ExperimentsModulePage() {
  const hw = useHardwareStatus()
  const { activeProtocol } = useZimonWorkspace()
  const videoRef = useRef<HTMLVideoElement>(null)
  const [root, setRoot] = useState('')
  const [items, setItems] = useState<RecordingItem[]>([])
  const [err, setErr] = useState('')
  const [search, setSearch] = useState('')
  const [dateFilter, setDateFilter] = useState<DateFilter>('all')
  const [protocolFilter, setProtocolFilter] = useState<string>('all')
  const [sel, setSel] = useState<RecordingItem | null>(null)
  const [tab, setTab] = useState<'summary' | 'metadata' | 'protocol' | 'export'>('summary')
  const [subTab, setSubTab] = useState<'timeline' | 'summary'>('timeline')
  const [videoErr, setVideoErr] = useState('')
  const [copyMsg, setCopyMsg] = useState('')

  const load = useCallback(async () => {
    setErr('')
    try {
      const r = await apiFetch<ListOut>('/api/recordings/list')
      setRoot(r.root)
      setItems(r.items)
      setSel((prev) => {
        if (prev && r.items.some((x) => x.relpath === prev.relpath)) return prev
        return r.items[0] ?? null
      })
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const protocolNames = useMemo(() => {
    const arr: string[] = ['all']
    if (activeProtocol?.name) arr.push(activeProtocol.name)
    return arr
  }, [activeProtocol?.name])

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    return items.filter((x) => {
      if (!inDateRange(x.modified_iso, dateFilter)) return false
      if (protocolFilter !== 'all') {
        const needle = protocolFilter.toLowerCase().slice(0, 8)
        if (needle && !x.name.toLowerCase().includes(needle)) return false
      }
      if (!q) return true
      return x.name.toLowerCase().includes(q) || x.relpath.toLowerCase().includes(q)
    })
  }, [items, search, dateFilter, protocolFilter, activeProtocol?.name])

  const videoSrc = sel ? recordingsMediaUrl(sel.relpath) : ''

  const fullPath = useMemo(() => {
    if (!sel) return ''
    if (sel.full_path) return sel.full_path
    if (!root) return sel.relpath
    const sep = root.includes('\\') ? '\\' : '/'
    return `${root.replace(/[/\\]+$/, '')}${sep}${sel.relpath.replace(/^[/\\]+/, '')}`
  }, [sel, root])

  const timelineModel = useMemo(() => {
    const phases = activeProtocol?.phases?.length ? activeProtocol.phases : []
    const total = phases.reduce((s, p) => s + p.durationS, 0) || 120
    const tracks: { type: StimulusType; label: string; segments: { start: number; len: number; on: boolean }[] }[] =
      [
        { type: 'light', label: 'Light', segments: [] },
        { type: 'buzzer', label: 'Buzzer', segments: [] },
        { type: 'vibration', label: 'Vibration', segments: [] },
        { type: 'water', label: 'Water', segments: [] },
      ]
    let acc = 0
    for (const ph of phases) {
      const len = ph.durationS
      const start = acc / total
      const w = len / total
      for (const tr of tracks) {
        const st = ph.stimuli.find((s) => s.type === tr.type)
        tr.segments.push({ start, len: w, on: !!st?.on })
      }
      acc += len
    }
    if (phases.length === 0) {
      for (const tr of tracks) {
        tr.segments.push({ start: 0, len: 1, on: false })
      }
    }
    return { total, tracks }
  }, [activeProtocol])

  async function copyPath() {
    if (!fullPath) return
    try {
      await navigator.clipboard.writeText(fullPath)
      setCopyMsg('Copied')
      window.setTimeout(() => setCopyMsg(''), 2000)
    } catch {
      setCopyMsg('Copy failed')
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-4 pb-10">
      <div
        className={[
          'rounded-xl border px-3 py-2 text-[11px]',
          hw.environmentOk ? 'border-emerald-500/25 text-emerald-200/90' : 'border-amber-500/30 text-amber-200/90',
        ].join(' ')}
      >
        {hw.environmentMessage} Playback uses authenticated media URLs; exports use paths from the API host.
      </div>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-zimon-fg dark:text-cyan-50/95">Experiments</h1>
          <p className="mt-1 text-xs text-zimon-muted">
            Library: <span className="font-mono text-cyan-200/80">{root || '—'}</span>
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-lg border border-zimon-border px-3 py-2 text-xs font-semibold dark:border-cyan-500/25"
        >
          Refresh list
        </button>
      </div>

      {err ? (
        <div className="rounded-lg border border-amber-500/35 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
          {err} — add videos under the recordings folder or set <code className="font-mono">ZIMON_RECORDINGS_ROOT</code>.
        </div>
      ) : null}

      <div className="grid min-h-0 grid-cols-1 gap-4 xl:grid-cols-12">
        <aside className="flex min-h-[280px] flex-col rounded-2xl border border-zimon-border bg-zimon-panel/80 dark:border-cyan-500/15 dark:bg-slate-950/40 xl:col-span-3">
          <div className="space-y-2 border-b border-zimon-border/60 p-3 dark:border-cyan-500/10">
            <select
              className="w-full rounded-lg border border-zimon-border bg-zimon-card px-2 py-2 text-xs dark:border-cyan-500/20"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value as DateFilter)}
            >
              <option value="all">All dates</option>
              <option value="24h">Last 24 hours</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
            </select>
            <select
              className="w-full rounded-lg border border-zimon-border bg-zimon-card px-2 py-2 text-xs dark:border-cyan-500/20"
              value={protocolFilter}
              onChange={(e) => setProtocolFilter(e.target.value)}
            >
              {protocolNames.map((p) => (
                <option key={p} value={p}>
                  {p === 'all' ? 'All protocols' : p}
                </option>
              ))}
            </select>
            <input
              type="search"
              placeholder="Search name…"
              className="w-full rounded-lg border border-zimon-border bg-zimon-card px-3 py-2 text-sm dark:border-cyan-500/20"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-[1fr_1fr_1fr] gap-0 border-b border-zimon-border/40 px-2 py-1.5 text-[9px] font-bold uppercase text-zimon-muted dark:border-cyan-500/10">
            <span>Date</span>
            <span className="col-span-2">Experiment</span>
          </div>
          <ul className="min-h-0 flex-1 overflow-y-auto p-1 text-xs">
            {filtered.length === 0 ? (
              <li className="p-3 text-zimon-muted">No recordings match filters.</li>
            ) : (
              filtered.map((x) => {
                const active = sel?.relpath === x.relpath
                const dt = new Date(x.modified_iso)
                return (
                  <li key={x.relpath}>
                    <button
                      type="button"
                      onClick={() => {
                        setSel(x)
                        setVideoErr('')
                      }}
                      className={[
                        'mb-0.5 grid w-full grid-cols-[1fr_1fr_1fr] gap-1 rounded-lg border px-2 py-2 text-left transition-colors',
                        active
                          ? 'border-cyan-400/50 bg-cyan-500/15'
                          : 'border-transparent hover:border-cyan-500/20 hover:bg-slate-900/50',
                      ].join(' ')}
                    >
                      <span className="text-[10px] text-zimon-muted">{dt.toLocaleDateString()}</span>
                      <span className="col-span-2 truncate font-mono text-[11px] font-semibold text-cyan-100/90">
                        {x.name}
                      </span>
                      <span className="text-[9px] text-emerald-400/90">Completed</span>
                      <span className="col-span-2 text-[9px] text-zimon-muted">
                        {(x.size / 1e6).toFixed(2)} MB
                      </span>
                    </button>
                  </li>
                )
              })
            )}
          </ul>
        </aside>

        <div className="flex min-h-0 flex-col gap-3 xl:col-span-6">
          <div className="relative flex min-h-[240px] flex-1 items-center justify-center overflow-hidden rounded-2xl border border-zimon-border bg-[#0a0c10] dark:border-cyan-500/15">
            {videoSrc ? (
              <video
                ref={videoRef}
                key={videoSrc}
                src={videoSrc}
                controls
                className="max-h-[min(52vh,480px)] w-full object-contain"
                onError={() => setVideoErr('Cannot play this file in the browser (codec).')}
              />
            ) : (
              <span className="text-sm text-zimon-muted">Select a recording</span>
            )}
            {videoErr ? (
              <div className="absolute bottom-12 left-2 right-2 rounded-lg bg-red-950/90 px-2 py-1 text-center text-[11px] text-red-200">
                {videoErr}
              </div>
            ) : null}
            <div className="absolute bottom-2 left-2 right-2 flex flex-wrap items-center justify-center gap-2">
              <button
                type="button"
                disabled={!sel}
                onClick={() => {
                  const v = videoRef.current
                  if (!v) return
                  void v.play()
                }}
                className="inline-flex items-center gap-1 rounded-lg bg-cyan-600/90 px-3 py-1.5 text-[11px] font-bold text-white disabled:opacity-40"
              >
                <Play className="h-3.5 w-3.5 fill-current" />
                Replay
              </button>
              <button
                type="button"
                onClick={() => {
                  const v = videoRef.current
                  if (!v) return
                  v.pause()
                }}
                className="rounded-lg border border-white/20 px-2 py-1.5 text-[11px] text-white/90"
              >
                Pause
              </button>
              <button
                type="button"
                onClick={() => {
                  const v = videoRef.current
                  if (!v) return
                  v.pause()
                  v.currentTime = 0
                }}
                className="inline-flex items-center gap-1 rounded-lg border border-white/20 px-2 py-1.5 text-[11px] text-white/90"
              >
                <Square className="h-3 w-3 fill-current" />
                Stop
              </button>
              <button
                type="button"
                onClick={() => {
                  const v = videoRef.current
                  if (!v) return
                  v.currentTime = Math.max(0, v.currentTime - 5)
                }}
                className="inline-flex items-center gap-1 rounded-lg border border-white/20 px-2 py-1.5 text-[11px] text-white/90"
              >
                <SkipBack className="h-3 w-3" />
                -5s
              </button>
            </div>
          </div>

          <div className="rounded-xl border border-zimon-border bg-zimon-panel/60 dark:border-cyan-500/15">
            <div className="flex border-b border-zimon-border/50 dark:border-cyan-500/10">
              {(
                [
                  ['timeline', 'Timeline'],
                  ['summary', 'Summary'],
                ] as const
              ).map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setSubTab(id)}
                  className={[
                    'flex-1 px-3 py-2 text-xs font-bold uppercase tracking-wide',
                    subTab === id ? 'border-b-2 border-cyan-400 text-cyan-200' : 'text-zimon-muted',
                  ].join(' ')}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="p-3">
              {subTab === 'summary' && (
                <ul className="space-y-1 text-[11px] text-zimon-muted">
                  <li>
                    <span className="text-zimon-fg">File</span> {sel?.name ?? '—'}
                  </li>
                  <li>
                    <span className="text-zimon-fg">Protocol ref</span> {activeProtocol?.name ?? '—'}
                  </li>
                  <li>
                    <span className="text-zimon-fg">Timeline scale</span> {timelineModel.total}s (from loaded protocol)
                  </li>
                </ul>
              )}
              {subTab === 'timeline' && (
                <div className="space-y-2">
                  <div className="flex justify-between text-[9px] font-bold uppercase text-zimon-muted">
                    <span>Baseline</span>
                    <span>Stimulus</span>
                    <span>Recovery</span>
                  </div>
                  {timelineModel.tracks.map((tr) => (
                    <div key={tr.type} className="flex items-center gap-2">
                      <span className="w-20 shrink-0 text-[10px] font-semibold text-zimon-fg">{tr.label}</span>
                      <div className="relative h-6 min-w-0 flex-1 overflow-hidden rounded-md bg-slate-900/90">
                        {tr.segments.map((seg, i) => (
                          <div
                            key={i}
                            className={[
                              'absolute top-0.5 bottom-0.5 rounded-sm border border-white/10',
                              seg.on ? 'bg-amber-500/70' : 'bg-slate-700/50',
                            ].join(' ')}
                            style={{
                              left: `${seg.start * 100}%`,
                              width: `${Math.max(0.5, seg.len * 100)}%`,
                            }}
                            title={seg.on ? 'ON' : 'OFF'}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                  <p className="text-[10px] text-zimon-muted">
                    Tracks reflect the active protocol in workspace. Load a protocol on Adult or Protocol Builder to
                    align markers.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        <aside className="rounded-2xl border border-zimon-border bg-zimon-panel/80 dark:border-cyan-500/15 dark:bg-slate-950/40 xl:col-span-3">
          <div className="flex border-b border-zimon-border/60 dark:border-cyan-500/10">
            {(
              [
                ['summary', 'Summary'],
                ['metadata', 'Metadata'],
                ['protocol', 'Protocol'],
                ['export', 'Export'],
              ] as const
            ).map(([id, label]) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                className={[
                  'flex-1 px-1 py-2 text-[9px] font-bold uppercase tracking-wide sm:text-[10px]',
                  tab === id ? 'border-b-2 border-cyan-400 text-cyan-300' : 'text-zimon-muted',
                ].join(' ')}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="p-3 text-xs">
            {tab === 'summary' && (
              <ul className="space-y-2 text-zimon-muted">
                <li>
                  <span className="text-zimon-fg">Pulse count</span> — (needs run log)
                </li>
                <li>
                  <span className="text-zimon-fg">Duration</span> Use player controls
                </li>
                <li>
                  <span className="text-zimon-fg">Triggers</span> — (needs run log)
                </li>
                <li>
                  <span className="text-zimon-fg">Notes</span> Files are served from the API recordings root.
                </li>
              </ul>
            )}
            {tab === 'metadata' && (
              <div className="space-y-3">
                <ul className="space-y-2 font-mono text-[11px] text-zimon-muted">
                  <li>
                    <span className="text-zimon-fg">Experiment ID</span>{' '}
                    {sel ? experimentIdFromFile(sel.name) : '—'}
                  </li>
                  <li>
                    <span className="text-zimon-fg">Recorded</span> {sel ? new Date(sel.modified_iso).toLocaleString() : '—'}
                  </li>
                  <li>
                    <span className="text-zimon-fg">Protocol</span> {activeProtocol?.name ?? '—'}
                  </li>
                  <li>
                    <span className="text-zimon-fg">Camera</span>{' '}
                    {hw.cameraSlots[0]?.cameraName ?? '—'}
                  </li>
                  <li>
                    <span className="text-zimon-fg">Path</span>
                    <div className="mt-1 break-all rounded-lg bg-slate-950/80 p-2 text-[10px] text-slate-400">
                      {fullPath || '—'}
                    </div>
                  </li>
                </ul>
                <button
                  type="button"
                  disabled={!fullPath}
                  onClick={() => void copyPath()}
                  className="flex w-full items-center justify-center gap-1 rounded-lg border border-cyan-500/35 bg-cyan-500/10 py-2 text-[11px] font-semibold text-cyan-100 disabled:opacity-40"
                >
                  <Copy className="h-3.5 w-3.5" />
                  Copy full path
                </button>
                {copyMsg ? <p className="text-[10px] text-emerald-400">{copyMsg}</p> : null}
              </div>
            )}
            {tab === 'protocol' && (
              <div className="text-zimon-muted">
                <p className="text-[11px]">Workspace protocol overview:</p>
                <pre className="mt-2 max-h-48 overflow-auto rounded-lg bg-slate-950/80 p-2 text-[10px] text-slate-400">
                  {activeProtocol ? JSON.stringify(activeProtocol.phases, null, 2) : 'None — load in Protocol Builder'}
                </pre>
              </div>
            )}
            {tab === 'export' && (
              <div className="space-y-2">
                <p className="text-[11px] text-zimon-muted">Server-side export endpoints can be added later.</p>
                <button
                  type="button"
                  disabled={!sel}
                  className="w-full rounded-lg border border-zimon-border py-2 text-xs font-semibold opacity-60 dark:border-cyan-500/20"
                >
                  Export CSV (soon)
                </button>
                <button
                  type="button"
                  disabled={!sel}
                  className="w-full rounded-lg border border-zimon-border py-2 text-xs font-semibold opacity-60 dark:border-cyan-500/20"
                >
                  Export logs (soon)
                </button>
                <button
                  type="button"
                  disabled={!sel}
                  className="w-full rounded-lg border border-zimon-border py-2 text-xs font-semibold opacity-60 dark:border-cyan-500/20"
                >
                  Export ZIP (soon)
                </button>
                <Link
                  to="/app/settings"
                  className="block w-full rounded-lg border border-zimon-border py-2 text-center text-xs font-semibold text-zimon-fg dark:border-cyan-500/20"
                >
                  Settings
                </Link>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}
