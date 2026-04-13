import { Copy, Play, RefreshCw, Search, SkipBack, Square } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch, recordingsMediaUrl } from '../api/client'
import { useHardwareStatus } from '../context/HardwareStatusContext'
import { useZimonWorkspace } from '../context/ZimonWorkspaceContext'
import type { PhaseKind, StimulusType } from '../types/zimonProtocol'

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
  const d = base.match(/(20\d{2})[_-]?(\d{2})[_-]?(\d{2})/)
  if (d) {
    const tail = base.match(/(\d+)(?!.*\d)/)
    const seq = tail ? String(tail[1]).slice(-2).padStart(2, '0') : '01'
    return `EXP_${d[1]}_${d[2]}${d[3]}_${seq}`
  }
  const safe = base.replace(/[^a-zA-Z0-9_-]+/g, '_').slice(0, 32)
  return `EXP_${safe || 'FILE'}`
}

function phaseBarClass(kind: PhaseKind): string {
  switch (kind) {
    case 'baseline':
      return 'bg-[#1e3a5f]/90'
    case 'stimulus':
      return 'bg-[#00C2FF]/90'
    case 'recovery':
      return 'bg-[#1e3a5f]/85'
    default:
      return 'bg-slate-700/90'
  }
}

function stimulusOnClass(type: StimulusType): string {
  switch (type) {
    case 'light':
      return 'bg-cyan-400/90 shadow-[0_0_12px_rgba(34,211,238,0.35)]'
    case 'buzzer':
      return 'bg-emerald-500/90 shadow-[0_0_12px_rgba(34,197,94,0.3)]'
    case 'vibration':
      return 'bg-amber-500/90 shadow-[0_0_12px_rgba(245,158,11,0.35)]'
    case 'water':
      return 'bg-sky-500/85 shadow-[0_0_12px_rgba(14,165,233,0.3)]'
    default:
      return 'bg-slate-500/80'
  }
}

function cameraShortLabel(slot: { label: string; cameraName: string | null } | undefined): string {
  if (!slot?.cameraName) return '—'
  const n = slot.cameraName
  if (/top|primary/i.test(n) && !/side/i.test(n)) return 'USB TOP'
  if (/side/i.test(n)) return 'USB SIDE'
  return n.length > 24 ? `${n.slice(0, 22)}…` : n
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
    const phaseBar: { start: number; len: number; kind: PhaseKind; label: string }[] =
      phases.length > 0
        ? (() => {
            let cumS = 0
            return phases.map((ph) => {
              const start = cumS / total
              const len = ph.durationS / total
              cumS += ph.durationS
              const label =
                ph.label?.trim() ||
                (ph.kind === 'baseline'
                  ? 'Baseline'
                  : ph.kind === 'stimulus'
                    ? 'Stimulus'
                    : 'Recovery')
              return { start, len, kind: ph.kind, label }
            })
          })()
        : [
            { start: 0, len: 1 / 3, kind: 'baseline' as const, label: 'Baseline' },
            { start: 1 / 3, len: 1 / 3, kind: 'stimulus' as const, label: 'Stimulus' },
            { start: 2 / 3, len: 1 / 3, kind: 'recovery' as const, label: 'Recovery' },
          ]
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
    return { total, phaseBar, tracks }
  }, [activeProtocol])

  const adultTopSlot = hw.cameraSlots.find((s) => s.key === 'adultTop')
  const timeTicks = useMemo(() => {
    const t = timelineModel.total
    const n = 5
    if (!Number.isFinite(t) || t <= 0) return [0, 0, 0, 0, 0]
    return Array.from({ length: n }, (_, i) => Math.round((t * i) / (n - 1)))
  }, [timelineModel.total])

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
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-5 pb-10">
      <div
        className={[
          'rounded-lg border px-3 py-2.5 text-[11px] leading-snug shadow-sm',
          hw.environmentOk
            ? 'border-emerald-500/30 bg-emerald-950/20 text-emerald-100/95'
            : 'border-amber-500/45 bg-[#1a1408]/80 text-amber-100/95',
        ].join(' ')}
      >
        <span className="font-medium">{hw.environmentMessage}</span>{' '}
        <span
          className={
            hw.environmentOk ? 'text-emerald-200/75' : 'text-amber-200/80 dark:text-amber-100/65'
          }
        >
          Playback uses authenticated media URLs; exports use paths from the API host.
        </span>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zimon-border/50 pb-4 dark:border-cyan-500/10">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-zimon-fg dark:text-white">Experiments</h1>
          <p className="mt-1 max-w-xl text-xs text-zimon-muted">
            Review recordings, replay capture, and align stimulus tracks with the protocol in your workspace.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="inline-flex items-center gap-2 rounded-lg border border-cyan-500/35 bg-slate-950/40 px-4 py-2 text-xs font-semibold text-cyan-100 transition-colors hover:border-cyan-400/50 hover:bg-cyan-500/10"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh list
        </button>
      </div>

      {err ? (
        <div className="rounded-lg border border-amber-500/35 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
          {err} — add videos under the recordings folder or set <code className="font-mono">ZIMON_RECORDINGS_ROOT</code>.
        </div>
      ) : null}

      <div className="grid min-h-0 grid-cols-1 gap-4 xl:grid-cols-12">
        <aside className="flex min-h-[300px] flex-col overflow-hidden rounded-2xl border border-zimon-border bg-zimon-panel/80 shadow-[inset_0_1px_0_rgba(56,189,248,0.06)] dark:border-cyan-500/15 dark:bg-[#0B0E14]/90 xl:col-span-3">
          <div className="space-y-2 border-b border-zimon-border/60 p-3 dark:border-cyan-500/10">
            <select
              className="w-full rounded-lg border border-zimon-border bg-zimon-card px-2 py-2 text-xs dark:border-cyan-500/20 dark:bg-slate-900/60"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value as DateFilter)}
            >
              <option value="all">All dates</option>
              <option value="24h">Last 24 hours</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
            </select>
            <select
              className="w-full rounded-lg border border-zimon-border bg-zimon-card px-2 py-2 text-xs dark:border-cyan-500/20 dark:bg-slate-900/60"
              value={protocolFilter}
              onChange={(e) => setProtocolFilter(e.target.value)}
            >
              {protocolNames.map((p) => (
                <option key={p} value={p}>
                  {p === 'all' ? 'All protocols' : p}
                </option>
              ))}
            </select>
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-zimon-muted" />
              <input
                type="search"
                placeholder="Search name…"
                className="w-full rounded-lg border border-zimon-border bg-zimon-card py-2 pl-8 pr-3 text-sm dark:border-cyan-500/20 dark:bg-slate-900/60"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-[2rem_4.5rem_1fr] gap-1 border-b border-zimon-border/40 px-2 py-2 text-[9px] font-bold uppercase tracking-wide text-zimon-muted dark:border-cyan-500/10">
            <span className="text-center">#</span>
            <span>Date</span>
            <span className="truncate">Experiment</span>
          </div>
          <ul className="min-h-0 flex-1 overflow-y-auto p-1.5 text-xs">
            {filtered.length === 0 ? (
              <li className="rounded-lg border border-dashed border-zimon-border/50 px-3 py-8 text-center text-[11px] text-zimon-muted dark:border-cyan-500/15">
                No recordings match filters.
              </li>
            ) : (
              filtered.map((x, idx) => {
                const active = sel?.relpath === x.relpath
                const dt = new Date(x.modified_iso)
                const expId = experimentIdFromFile(x.name)
                return (
                  <li key={x.relpath}>
                    <button
                      type="button"
                      onClick={() => {
                        setSel(x)
                        setVideoErr('')
                      }}
                      className={[
                        'mb-1 grid w-full grid-cols-[2rem_4.5rem_1fr] items-start gap-1 rounded-lg border px-2 py-2 text-left transition-colors',
                        active
                          ? 'border-cyan-400/45 bg-cyan-500/12 shadow-[0_0_20px_-8px_rgba(34,211,238,0.5)]'
                          : 'border-transparent hover:border-cyan-500/25 hover:bg-slate-900/55',
                      ].join(' ')}
                    >
                      <span className="pt-0.5 text-center text-[10px] font-semibold tabular-nums text-zimon-muted">
                        {idx + 1}
                      </span>
                      <span className="pt-0.5 text-[10px] leading-tight text-zimon-muted">
                        {dt.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                      </span>
                      <span className="min-w-0">
                        <span className="block truncate font-mono text-[11px] font-semibold text-cyan-100/95">
                          {expId}
                        </span>
                        <span className="mt-0.5 block truncate text-[9px] text-zimon-muted">{x.name}</span>
                      </span>
                    </button>
                  </li>
                )
              })
            )}
          </ul>
        </aside>

        <div className="flex min-h-0 flex-col gap-3 xl:col-span-6">
          <div className="relative flex min-h-[min(52vh,420px)] flex-1 items-center justify-center overflow-hidden rounded-2xl border border-zimon-border bg-[#0B0E14] shadow-inner dark:border-cyan-500/12">
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
              <span className="text-sm font-medium text-slate-500">Select a recording</span>
            )}
            {videoErr ? (
              <div className="absolute bottom-14 left-2 right-2 rounded-lg bg-red-950/90 px-2 py-1 text-center text-[11px] text-red-200">
                {videoErr}
              </div>
            ) : null}
            <div className="absolute bottom-3 left-2 right-2 flex flex-wrap items-center justify-center gap-2">
              <button
                type="button"
                disabled={!sel}
                onClick={() => {
                  const v = videoRef.current
                  if (!v) return
                  void v.play()
                }}
                className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500 px-4 py-2 text-[11px] font-bold text-white shadow-lg shadow-emerald-900/40 transition-colors hover:bg-emerald-400 disabled:opacity-40"
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
                className="rounded-lg border border-cyan-500/35 bg-slate-950/70 px-3 py-2 text-[11px] font-semibold text-slate-100 backdrop-blur-sm hover:border-cyan-400/45 hover:bg-slate-900/90"
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
                className="inline-flex items-center gap-1 rounded-lg border border-cyan-500/35 bg-slate-950/70 px-3 py-2 text-[11px] font-semibold text-slate-100 backdrop-blur-sm hover:border-cyan-400/45"
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
                className="inline-flex items-center gap-1 rounded-lg border border-cyan-500/35 bg-slate-950/70 px-3 py-2 text-[11px] font-semibold text-slate-100 backdrop-blur-sm hover:border-cyan-400/45"
              >
                <SkipBack className="h-3 w-3" />
                −5s
              </button>
            </div>
          </div>

          <div className="overflow-hidden rounded-xl border border-zimon-border bg-zimon-panel/60 dark:border-cyan-500/15 dark:bg-[#0B0E14]/70">
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
                    'flex-1 px-3 py-2.5 text-[10px] font-bold uppercase tracking-[0.12em]',
                    subTab === id ? 'border-b-2 border-[#00C2FF] text-cyan-100' : 'text-zimon-muted hover:text-slate-300',
                  ].join(' ')}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="p-3">
              {subTab === 'summary' && (
                <ul className="space-y-2 text-[11px] text-zimon-muted">
                  <li>
                    <span className="font-semibold text-zimon-fg dark:text-slate-200">File</span>{' '}
                    <span className="font-mono text-cyan-200/80">{sel?.name ?? '—'}</span>
                  </li>
                  <li>
                    <span className="font-semibold text-zimon-fg dark:text-slate-200">Protocol ref</span>{' '}
                    {activeProtocol?.name ?? '—'}
                  </li>
                  <li>
                    <span className="font-semibold text-zimon-fg dark:text-slate-200">Timeline scale</span>{' '}
                    {timelineModel.total}s <span className="text-zimon-muted">(from workspace protocol)</span>
                  </li>
                  <li className="border-t border-zimon-border/40 pt-2 text-[10px] dark:border-cyan-500/10">
                    Library root:{' '}
                    <span className="break-all font-mono text-[10px] text-slate-400">{root || '—'}</span>
                  </li>
                </ul>
              )}
              {subTab === 'timeline' && (
                <div className="space-y-3">
                  <div>
                    <p className="mb-1.5 text-[9px] font-bold uppercase tracking-wide text-zimon-muted">Phases</p>
                    <div className="relative h-8 w-full overflow-hidden rounded-lg border border-white/5 bg-slate-950/90">
                      {timelineModel.phaseBar.map((seg, i) => (
                        <div
                          key={i}
                          className={[
                            'absolute top-0 flex h-full items-center justify-center border-r border-black/20 text-[9px] font-bold uppercase tracking-tight text-white/95 last:border-r-0',
                            phaseBarClass(seg.kind),
                          ].join(' ')}
                          style={{
                            left: `${seg.start * 100}%`,
                            width: `${Math.max(0.4, seg.len * 100)}%`,
                          }}
                          title={seg.label}
                        >
                          <span className="truncate px-1">{seg.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  {timelineModel.tracks.map((tr) => (
                    <div key={tr.type} className="flex items-center gap-2">
                      <span className="w-[4.5rem] shrink-0 text-[10px] font-semibold text-slate-200">{tr.label}</span>
                      <div className="relative h-7 min-w-0 flex-1 overflow-hidden rounded-md border border-slate-700/50 bg-[#06080c]">
                        {tr.segments.map((seg, i) => (
                          <div
                            key={i}
                            className={[
                              'absolute top-1 bottom-1 rounded-sm border',
                              seg.on ? stimulusOnClass(tr.type) : 'border-white/5 bg-slate-800/60',
                            ].join(' ')}
                            style={{
                              left: `${seg.start * 100}%`,
                              width: `${Math.max(0.35, seg.len * 100)}%`,
                            }}
                            title={seg.on ? 'ON' : 'OFF'}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                  <div className="relative pt-1">
                    <div className="flex justify-between border-t border-slate-700/40 pt-1 text-[9px] tabular-nums text-zimon-muted">
                      {timeTicks.map((s, i) => (
                        <span key={i}>{s}s</span>
                      ))}
                    </div>
                  </div>
                  <p className="text-[10px] leading-relaxed text-zimon-muted">
                    Tracks reflect the active protocol in workspace. Load a protocol on Adult or Protocol Builder to
                    align markers.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        <aside className="flex min-h-[280px] flex-col rounded-2xl border border-zimon-border bg-zimon-panel/80 shadow-[inset_0_1px_0_rgba(56,189,248,0.06)] dark:border-cyan-500/15 dark:bg-[#0B0E14]/90 xl:col-span-3">
          <div className="flex shrink-0 overflow-x-auto border-b border-zimon-border/60 dark:border-cyan-500/10">
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
                  'min-w-[4.25rem] flex-1 whitespace-nowrap px-1.5 py-2.5 text-[9px] font-bold uppercase tracking-[0.1em] sm:min-w-0 sm:text-[10px]',
                  tab === id ? 'border-b-2 border-[#00C2FF] text-cyan-100' : 'text-zimon-muted hover:text-slate-300',
                ].join(' ')}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto p-3 text-xs">
            {tab === 'summary' && (
              <ul className="space-y-3 text-[11px] leading-relaxed text-zimon-muted">
                <li>
                  <span className="font-semibold text-zimon-fg dark:text-slate-200">Pulse count</span> — (needs run log)
                </li>
                <li>
                  <span className="font-semibold text-zimon-fg dark:text-slate-200">Duration</span>{' '}
                  <span className="text-slate-400">Use player controls for timing.</span>
                </li>
                <li>
                  <span className="font-semibold text-zimon-fg dark:text-slate-200">Triggers</span> — (needs run log)
                </li>
                <li className="border-t border-zimon-border/40 pt-3 text-[10px] dark:border-cyan-500/10">
                  <span className="font-semibold text-zimon-fg dark:text-slate-200">Notes</span> Files are served from the
                  API recordings root.
                </li>
              </ul>
            )}
            {tab === 'metadata' && (
              <div className="space-y-4">
                <dl className="space-y-3 text-[11px]">
                  <div>
                    <dt className="text-[9px] font-bold uppercase tracking-wide text-zimon-muted">Experiment ID</dt>
                    <dd className="mt-0.5 font-mono text-sm font-semibold text-cyan-100/95">
                      {sel ? experimentIdFromFile(sel.name) : '—'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-[9px] font-bold uppercase tracking-wide text-zimon-muted">Camera</dt>
                    <dd className="mt-0.5 text-slate-200">{cameraShortLabel(adultTopSlot)}</dd>
                  </div>
                  <div>
                    <dt className="text-[9px] font-bold uppercase tracking-wide text-zimon-muted">Start</dt>
                    <dd className="mt-0.5 font-mono text-[11px] text-slate-300">
                      {sel
                        ? new Date(sel.modified_iso).toLocaleString(undefined, {
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit',
                          })
                        : '—'}
                    </dd>
                    <p className="mt-0.5 text-[9px] text-zimon-muted">From file timestamp (session log not attached).</p>
                  </div>
                  <div>
                    <dt className="text-[9px] font-bold uppercase tracking-wide text-zimon-muted">End</dt>
                    <dd className="mt-0.5 font-mono text-[11px] text-slate-500">—</dd>
                  </div>
                  <div>
                    <dt className="text-[9px] font-bold uppercase tracking-wide text-zimon-muted">Protocol</dt>
                    <dd className="mt-0.5 text-slate-300">{activeProtocol?.name ?? '—'}</dd>
                  </div>
                  <div>
                    <dt className="text-[9px] font-bold uppercase tracking-wide text-zimon-muted">Folder</dt>
                    <dd className="mt-1 break-all rounded-lg border border-white/5 bg-slate-950/85 p-2.5 font-mono text-[10px] leading-snug text-slate-400">
                      {fullPath || '—'}
                    </dd>
                  </div>
                </dl>
                <button
                  type="button"
                  disabled={!fullPath}
                  onClick={() => void copyPath()}
                  className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-cyan-500/35 bg-cyan-500/10 py-2.5 text-[11px] font-semibold text-cyan-100 transition-colors hover:border-cyan-400/50 hover:bg-cyan-500/15 disabled:opacity-40"
                >
                  <Copy className="h-3.5 w-3.5" />
                  Copy full path
                </button>
                {copyMsg ? <p className="text-center text-[10px] text-emerald-400">{copyMsg}</p> : null}
              </div>
            )}
            {tab === 'protocol' && (
              <div className="text-zimon-muted">
                <p className="text-[11px] text-slate-400">
                  Phases and stimuli from the workspace protocol (Adult / Protocol Builder).
                </p>
                <pre className="mt-2 max-h-52 overflow-auto rounded-lg border border-white/5 bg-slate-950/90 p-3 text-[10px] leading-relaxed text-slate-400">
                  {activeProtocol ? JSON.stringify(activeProtocol.phases, null, 2) : 'None — load in Protocol Builder'}
                </pre>
              </div>
            )}
            {tab === 'export' && (
              <div className="space-y-2">
                <p className="text-[11px] leading-relaxed text-zimon-muted">
                  Server-side export endpoints can be added later. Paths always resolve on the API host.
                </p>
                <button
                  type="button"
                  disabled={!sel}
                  className="w-full rounded-lg border border-cyan-500/20 py-2.5 text-xs font-semibold text-slate-400 opacity-60 dark:border-cyan-500/25"
                >
                  Export CSV (soon)
                </button>
                <button
                  type="button"
                  disabled={!sel}
                  className="w-full rounded-lg border border-cyan-500/20 py-2.5 text-xs font-semibold text-slate-400 opacity-60 dark:border-cyan-500/25"
                >
                  Export logs (soon)
                </button>
                <button
                  type="button"
                  disabled={!sel}
                  className="w-full rounded-lg border border-cyan-500/20 py-2.5 text-xs font-semibold text-slate-400 opacity-60 dark:border-cyan-500/25"
                >
                  Export ZIP (soon)
                </button>
                <Link
                  to="/app/settings"
                  className="block w-full rounded-lg border border-cyan-500/35 py-2.5 text-center text-xs font-semibold text-cyan-100 transition-colors hover:border-cyan-400/50 hover:bg-cyan-500/10"
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
