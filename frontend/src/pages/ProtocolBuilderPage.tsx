import { Loader2, Play } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useHardwareStatus } from '../context/HardwareStatusContext'
import { buildDefaultProtocol } from '../features/protocol-builder/buildDefaultProtocol'
import {
  deleteProtocolFromLibrary,
  duplicateProtocol,
  loadProtocolLibrary,
  upsertProtocol,
} from '../features/protocol-builder/protocolStorage'
import { validateProtocol } from '../features/protocol-builder/protocolValidation'
import { useZimonWorkspace } from '../context/ZimonWorkspaceContext'
import type { PhaseKind, ProtocolPhase, StimulusConfig, StimulusType, ZimonProtocol } from '../types/zimonProtocol'
import { defaultStimulus, newPhaseId } from '../types/zimonProtocol'
import { pulseBuzzer, pulseIr, pulsePump, pulseVibration } from '../utils/hardwarePulse'

const STIM_LABELS: Record<StimulusType, string> = {
  light: 'Light',
  buzzer: 'Buzzer',
  vibration: 'Vibration',
  water: 'Water Flow',
}

export function ProtocolBuilderPage() {
  const hw = useHardwareStatus()
  const { setActiveProtocol } = useZimonWorkspace()
  const [protocol, setProtocol] = useState<ZimonProtocol>(() => buildDefaultProtocol())
  const [library, setLibrary] = useState(() => loadProtocolLibrary())
  const [selPhaseId, setSelPhaseId] = useState<string | null>(() => protocol.phases[0]?.id ?? null)
  const [selStimType, setSelStimType] = useState<StimulusType>('light')
  const [testBusy, setTestBusy] = useState(false)
  const [testNote, setTestNote] = useState('')

  const selectedPhase = protocol.phases.find((p) => p.id === selPhaseId) ?? protocol.phases[0] ?? null
  const selectedStimulus = selectedPhase?.stimuli.find((s) => s.type === selStimType)

  const issues = useMemo(() => validateProtocol(protocol), [protocol])
  const jsonPreview = useMemo(() => JSON.stringify(protocol, null, 2), [protocol])
  const totalRuntimeS = useMemo(
    () => protocol.phases.reduce((s, ph) => s + ph.durationS, 0),
    [protocol.phases],
  )

  const refreshLibrary = () => setLibrary(loadProtocolLibrary())

  const updatePhase = useCallback((id: string, u: Partial<ProtocolPhase>) => {
    setProtocol((p) => ({
      ...p,
      phases: p.phases.map((ph) => (ph.id === id ? { ...ph, ...u } : ph)),
    }))
  }, [])

  const updateStimulus = useCallback((phaseId: string, type: StimulusType, u: Partial<StimulusConfig>) => {
    setProtocol((p) => ({
      ...p,
      phases: p.phases.map((ph) =>
        ph.id === phaseId
          ? {
              ...ph,
              stimuli: ph.stimuli.map((s) => (s.type === type ? { ...s, ...u } : s)),
            }
          : ph,
      ),
    }))
  }, [])

  const addPhase = (kind: PhaseKind) => {
    const ph: ProtocolPhase = {
      id: newPhaseId(),
      kind,
      durationS: 60,
      label: kind.charAt(0).toUpperCase() + kind.slice(1),
      stimuli: [
        defaultStimulus('light'),
        defaultStimulus('buzzer'),
        defaultStimulus('vibration'),
        defaultStimulus('water'),
      ],
    }
    setProtocol((p) => ({ ...p, phases: [...p.phases, ph] }))
    setSelPhaseId(ph.id)
  }

  const addHardwareStep = useCallback((label: string, durationS: number, prime: StimulusType) => {
    const ph: ProtocolPhase = {
      id: newPhaseId(),
      kind: 'stimulus',
      durationS,
      label,
      stimuli: [
        { ...defaultStimulus('light'), on: prime === 'light', intensity: prime === 'light' ? 80 : 0 },
        { ...defaultStimulus('buzzer'), on: prime === 'buzzer', intensity: prime === 'buzzer' ? 70 : 0 },
        { ...defaultStimulus('vibration'), on: prime === 'vibration', intensity: prime === 'vibration' ? 50 : 0 },
        { ...defaultStimulus('water'), on: prime === 'water', intensity: prime === 'water' ? 60 : 0 },
      ],
    }
    setProtocol((p) => ({ ...p, phases: [...p.phases, ph] }))
    setSelPhaseId(ph.id)
    setSelStimType(prime)
  }, [])

  const runHardwareTestSequence = useCallback(async () => {
    setTestNote('')
    if (!hw.stimulusPathOk) {
      setTestNote('Connect Arduino (Settings → serial) to run hardware tests.')
      return
    }
    if (hw.cameras.length === 0) {
      setTestNote('No camera enumerated — stimulus test will still run; add a camera for full checks.')
    }
    setTestBusy(true)
    try {
      await pulseIr(50)
      await new Promise((r) => setTimeout(r, 350))
      await pulseBuzzer(50)
      await new Promise((r) => setTimeout(r, 350))
      await pulseVibration(45)
      await new Promise((r) => setTimeout(r, 350))
      await pulsePump(40)
      setTestNote('Test sequence completed — verify chamber response.')
    } catch (e) {
      setTestNote(e instanceof Error ? e.message : String(e))
    } finally {
      setTestBusy(false)
      void hw.refresh()
    }
  }, [hw])

  const removePhase = (id: string) => {
    setProtocol((p) => {
      const nextPhases = p.phases.filter((x) => x.id !== id)
      setSelPhaseId((sel) => (sel === id ? nextPhases[0]?.id ?? null : sel))
      return { ...p, phases: nextPhases }
    })
  }

  const saveProtocol = () => {
    upsertProtocol(protocol)
    setActiveProtocol(protocol)
    refreshLibrary()
  }

  const saveAsDraft = () => {
    upsertProtocol({ ...protocol, name: protocol.name.trim() || 'Draft' })
    refreshLibrary()
  }

  const dup = () => {
    const next = duplicateProtocol(protocol)
    setProtocol(next)
    upsertProtocol(next)
    refreshLibrary()
  }

  const del = () => {
    if (!confirm('Delete this protocol from the library?')) return
    deleteProtocolFromLibrary(protocol.id)
    const next = buildDefaultProtocol()
    setProtocol(next)
    setSelPhaseId(next.phases[0]?.id ?? null)
    setActiveProtocol(null)
    refreshLibrary()
  }

  const loadFromLibrary = (id: string) => {
    const p = library.find((x) => x.id === id)
    if (p) {
      setProtocol(p)
      setSelPhaseId(p.phases[0]?.id ?? null)
    }
  }

  const downloadJson = () => {
    const blob = new Blob([jsonPreview], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `${protocol.name.replace(/\s+/g, '_') || 'protocol'}.json`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-4 pb-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-zimon-fg dark:text-cyan-50/95">Protocol Builder</h1>
          <p className="mt-1 text-xs text-zimon-muted">Design phases, attach stimuli, validate, and export JSON.</p>
        </div>
        <Link to="/app/adult" className="text-xs font-semibold text-cyan-400 hover:underline">
          ← Adult module
        </Link>
      </div>

      <div
        className={[
          'rounded-xl border px-4 py-3',
          hw.readyForExperiment
            ? 'border-emerald-500/35 bg-emerald-500/10 dark:border-emerald-500/25'
            : 'border-amber-500/40 bg-amber-500/10 dark:border-amber-500/25',
        ].join(' ')}
      >
        <p className="text-sm font-semibold text-zimon-fg">
          {hw.readyForExperiment ? 'Hardware linked — test run will command real outputs.' : 'Hardware incomplete — connect Arduino + camera for full operation.'}
        </p>
        <p className="mt-1 text-[11px] text-zimon-muted">{hw.environmentMessage}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        {/* A — Protocol details */}
        <section className="rounded-2xl border border-zimon-border bg-zimon-panel/80 p-4 dark:border-cyan-500/15 dark:bg-slate-950/40 xl:col-span-3">
          <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted">Protocol details</h2>
          <label className="mt-3 block text-xs text-zimon-muted">Name</label>
          <input
            className="mt-1 w-full rounded-lg border border-zimon-border bg-zimon-card px-3 py-2 text-sm dark:border-cyan-500/20"
            value={protocol.name}
            onChange={(e) => setProtocol((p) => ({ ...p, name: e.target.value }))}
          />
          <label className="mt-3 block text-xs text-zimon-muted">Description</label>
          <textarea
            className="mt-1 min-h-[88px] w-full rounded-lg border border-zimon-border bg-zimon-card px-3 py-2 text-sm dark:border-cyan-500/20"
            value={protocol.description}
            onChange={(e) => setProtocol((p) => ({ ...p, description: e.target.value }))}
          />
          <div className="mt-3 flex flex-col gap-2">
            <button
              type="button"
              onClick={saveProtocol}
              className="rounded-xl bg-gradient-to-r from-blue-600 to-sky-500 py-2.5 text-sm font-bold text-white shadow-md"
            >
              Save protocol
            </button>
            <button
              type="button"
              onClick={saveAsDraft}
              className="rounded-xl border border-zimon-border py-2 text-sm font-semibold dark:border-cyan-500/20"
            >
              Save as draft
            </button>
            <button
              type="button"
              onClick={dup}
              className="rounded-xl border border-zimon-border py-2 text-sm font-semibold dark:border-cyan-500/20"
            >
              Duplicate protocol
            </button>
            <button
              type="button"
              onClick={del}
              className="rounded-xl border border-red-500/40 py-2 text-sm font-semibold text-red-300"
            >
              Delete from library
            </button>
          </div>
          <label className="mt-4 block text-[10px] font-bold uppercase text-zimon-muted">Load saved</label>
          <select
            className="mt-1 w-full rounded-lg border border-zimon-border bg-zimon-card px-2 py-2 text-sm dark:border-cyan-500/20"
            value=""
            onChange={(e) => {
              loadFromLibrary(e.target.value)
              e.target.value = ''
            }}
          >
            <option value="">Select…</option>
            {library.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <button type="button" onClick={refreshLibrary} className="mt-2 w-full text-xs text-cyan-400 hover:underline">
            Refresh library list
          </button>
        </section>

        {/* B — Timeline */}
        <section className="rounded-2xl border border-zimon-border bg-zimon-panel/80 p-4 dark:border-cyan-500/15 dark:bg-slate-950/40 xl:col-span-4">
          <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted">Timeline</h2>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="w-full text-[10px] font-semibold uppercase tracking-wide text-zimon-muted">Add hardware step</span>
            <button
              type="button"
              onClick={() => addHardwareStep('Light flash', 2, 'light')}
              className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-[11px] font-semibold text-amber-100"
            >
              Light
            </button>
            <button
              type="button"
              onClick={() => addHardwareStep('Buzzer pulse', 1, 'buzzer')}
              className="rounded-lg border border-sky-500/30 bg-sky-500/10 px-2 py-1 text-[11px] font-semibold text-sky-100"
            >
              Buzzer
            </button>
            <button
              type="button"
              onClick={() => addHardwareStep('Vibration', 3, 'vibration')}
              className="rounded-lg border border-violet-500/30 bg-violet-500/10 px-2 py-1 text-[11px] font-semibold text-violet-100"
            >
              Vibration
            </button>
            <button
              type="button"
              onClick={() => addHardwareStep('Water flow', 4, 'water')}
              className="rounded-lg border border-cyan-500/30 bg-cyan-500/10 px-2 py-1 text-[11px] font-semibold text-cyan-100"
            >
              Water flow
            </button>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => addPhase('baseline')}
              className="rounded-lg border border-zimon-border px-3 py-1.5 text-xs font-semibold dark:border-cyan-500/25"
            >
              + Baseline
            </button>
            <button
              type="button"
              onClick={() => addPhase('stimulus')}
              className="rounded-lg border border-sky-500/30 bg-sky-500/10 px-3 py-1.5 text-xs font-semibold text-sky-200"
            >
              + Stimulus
            </button>
            <button
              type="button"
              onClick={() => addPhase('recovery')}
              className="rounded-lg border border-violet-500/30 bg-violet-500/10 px-3 py-1.5 text-xs font-semibold text-violet-200"
            >
              + Recovery
            </button>
          </div>
          <div className="mt-4 space-y-2">
            {protocol.phases.map((ph, idx) => {
              const total = protocol.phases.reduce((s, x) => s + x.durationS, 0) || 1
              const w = (ph.durationS / total) * 100
              const sel = ph.id === selectedPhase?.id
              return (
                <div
                  key={ph.id}
                  className={[
                    'rounded-xl border p-3 transition-colors',
                    sel ? 'border-cyan-400/50 bg-cyan-500/10' : 'border-zimon-border/60 bg-zimon-card/30',
                  ].join(' ')}
                >
                  <button type="button" className="w-full text-left" onClick={() => setSelPhaseId(ph.id)}>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-bold text-zimon-fg">
                        {idx + 1}. {ph.label || ph.kind}
                      </span>
                      <span className="text-[10px] text-zimon-muted">{ph.durationS}s</span>
                    </div>
                    <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-slate-800">
                      <div
                        className={[
                          'h-full rounded-full',
                          ph.kind === 'stimulus'
                            ? 'bg-sky-500'
                            : ph.kind === 'recovery'
                              ? 'bg-violet-500'
                              : 'bg-slate-500',
                        ].join(' ')}
                        style={{ width: `${Math.max(4, w)}%` }}
                      />
                    </div>
                  </button>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <label className="flex items-center gap-1 text-[11px] text-zimon-muted">
                      Duration (s)
                      <input
                        type="number"
                        min={1}
                        className="w-16 rounded border border-zimon-border bg-slate-900/60 px-1 py-0.5 text-xs"
                        value={ph.durationS}
                        onChange={(e) => updatePhase(ph.id, { durationS: Math.max(1, Number(e.target.value)) })}
                      />
                    </label>
                    <input
                      className="min-w-0 flex-1 rounded border border-zimon-border bg-slate-900/60 px-2 py-1 text-xs"
                      placeholder="Label"
                      value={ph.label || ''}
                      onChange={(e) => updatePhase(ph.id, { label: e.target.value })}
                    />
                    <button
                      type="button"
                      onClick={() => removePhase(ph.id)}
                      className="text-xs text-red-400 hover:underline"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </section>

        {/* C — Stimulus configuration */}
        <section className="rounded-2xl border border-zimon-border bg-zimon-panel/80 p-4 dark:border-cyan-500/15 dark:bg-slate-950/40 xl:col-span-3">
          <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted">Stimulus (selected phase)</h2>
          {!selectedPhase || !selectedStimulus ? (
            <p className="mt-3 text-sm text-zimon-muted">Select a phase.</p>
          ) : (
            <>
              <div className="mt-3 flex flex-wrap gap-1">
                {(Object.keys(STIM_LABELS) as StimulusType[]).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setSelStimType(t)}
                    className={[
                      'rounded-lg px-2.5 py-1 text-[11px] font-semibold',
                      selStimType === t ? 'bg-cyan-600/40 text-cyan-50' : 'bg-slate-800/80 text-slate-400',
                    ].join(' ')}
                  >
                    {STIM_LABELS[t]}
                  </button>
                ))}
              </div>
              <div className="mt-4 space-y-3 text-sm">
                <label className="flex items-center gap-2 text-xs">
                  <input
                    type="checkbox"
                    checked={selectedStimulus.on}
                    onChange={(e) => updateStimulus(selectedPhase.id, selStimType, { on: e.target.checked })}
                  />
                  ON for this phase
                </label>
                <label className="block text-xs text-zimon-muted">
                  Intensity (0–100)
                  <input
                    type="range"
                    min={0}
                    max={100}
                    className="mt-1 block w-full accent-cyan-500"
                    value={selectedStimulus.intensity}
                    onChange={(e) => updateStimulus(selectedPhase.id, selStimType, { intensity: Number(e.target.value) })}
                  />
                </label>
                <label className="block text-xs text-zimon-muted">
                  Frequency (Hz)
                  <input
                    type="number"
                    min={0}
                    className="mt-1 w-full rounded border border-zimon-border bg-zimon-card px-2 py-1"
                    value={selectedStimulus.frequencyHz}
                    onChange={(e) => updateStimulus(selectedPhase.id, selStimType, { frequencyHz: Number(e.target.value) })}
                  />
                </label>
                <label className="block text-xs text-zimon-muted">
                  Pulse width (ms)
                  <input
                    type="number"
                    min={0}
                    className="mt-1 w-full rounded border border-zimon-border bg-zimon-card px-2 py-1"
                    value={selectedStimulus.pulseWidthMs}
                    onChange={(e) =>
                      updateStimulus(selectedPhase.id, selStimType, { pulseWidthMs: Number(e.target.value) })
                    }
                  />
                </label>
                <label className="block text-xs text-zimon-muted">
                  Duration (ms)
                  <input
                    type="number"
                    min={0}
                    className="mt-1 w-full rounded border border-zimon-border bg-zimon-card px-2 py-1"
                    value={selectedStimulus.durationMs}
                    onChange={(e) => updateStimulus(selectedPhase.id, selStimType, { durationMs: Number(e.target.value) })}
                  />
                </label>
                <label className="block text-xs text-zimon-muted">
                  Delay (ms)
                  <input
                    type="number"
                    min={0}
                    className="mt-1 w-full rounded border border-zimon-border bg-zimon-card px-2 py-1"
                    value={selectedStimulus.delayMs}
                    onChange={(e) => updateStimulus(selectedPhase.id, selStimType, { delayMs: Number(e.target.value) })}
                  />
                </label>
                <label className="block text-xs text-zimon-muted">
                  Repetitions
                  <input
                    type="number"
                    min={1}
                    className="mt-1 w-full rounded border border-zimon-border bg-zimon-card px-2 py-1"
                    value={selectedStimulus.repetitions}
                    onChange={(e) =>
                      updateStimulus(selectedPhase.id, selStimType, { repetitions: Math.max(1, Number(e.target.value)) })
                    }
                  />
                </label>
              </div>
            </>
          )}
        </section>

        <section className="rounded-2xl border border-cyan-500/20 bg-slate-950/50 p-4 dark:border-cyan-500/25 dark:bg-slate-950/60 xl:col-span-2">
          <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted">Protocol summary</h2>
          <p className="mt-2 text-2xl font-bold tabular-nums text-cyan-100">{totalRuntimeS}s</p>
          <p className="text-[10px] text-zimon-muted">Total runtime</p>
          <ul className="mt-3 max-h-40 space-y-1.5 overflow-y-auto text-[11px] text-zimon-muted">
            {protocol.phases.map((ph, i) => (
              <li key={ph.id} className="flex justify-between gap-2 border-b border-white/5 pb-1">
                <span className="truncate text-zimon-fg">
                  {i + 1}. {ph.label || ph.kind}
                </span>
                <span className="shrink-0 tabular-nums">{ph.durationS}s</span>
              </li>
            ))}
          </ul>
          <button
            type="button"
            disabled={testBusy || !hw.stimulusPathOk}
            title={!hw.stimulusPathOk ? 'Connect Arduino first' : 'Fire a short IR → buzzer → vibration → pump sequence'}
            onClick={() => void runHardwareTestSequence()}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-sky-500 py-2.5 text-sm font-bold text-white shadow-md disabled:opacity-40"
          >
            {testBusy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-current" />}
            Test run
          </button>
          <button
            type="button"
            onClick={saveProtocol}
            className="mt-2 w-full rounded-xl border border-cyan-500/40 py-2 text-xs font-bold text-cyan-100"
          >
            Save protocol
          </button>
          {testNote ? <p className="mt-2 text-[10px] text-amber-200/90">{testNote}</p> : null}
        </section>
      </div>

      {/* D — Validation + JSON */}
      <section className="rounded-2xl border border-zimon-border bg-zimon-panel/80 p-4 dark:border-cyan-500/15 dark:bg-slate-950/40">
        <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted">Validation &amp; output</h2>
        {issues.length ? (
          <ul className="mt-2 list-inside list-disc text-xs text-amber-200/90">
            {issues.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-xs text-emerald-400/90">No blocking issues detected.</p>
        )}
        <textarea
          readOnly
          className="mt-3 h-48 w-full resize-y rounded-lg border border-zimon-border bg-slate-950/80 p-3 font-mono text-[11px] text-slate-300"
          value={jsonPreview}
        />
        <button
          type="button"
          onClick={downloadJson}
          className="mt-3 rounded-xl border border-cyan-500/40 bg-cyan-500/15 px-4 py-2 text-sm font-bold text-cyan-100"
        >
          Generate protocol JSON (download)
        </button>
      </section>
    </div>
  )
}
