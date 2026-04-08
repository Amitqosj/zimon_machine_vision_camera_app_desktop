import { Camera, Check, ChevronRight, Lightbulb, Loader2, Video, Waves } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { useHardwareStatus } from '../../context/HardwareStatusContext'
import {
  pulseBuzzer,
  pulseIr,
  pulsePump,
  pulseVibration,
  testCameraPreview,
} from '../../utils/hardwarePulse'

export function ReadinessDashboard() {
  const hw = useHardwareStatus()
  const [logLines, setLogLines] = useState<string[]>([])
  const [busy, setBusy] = useState<string | null>(null)

  const pushLog = useCallback((line: string) => {
    setLogLines((prev) => [`${new Date().toLocaleTimeString()} ${line}`, ...prev].slice(0, 50))
  }, [])

  const readinessPct = useMemo(() => {
    let s = 0
    if (hw.arduinoOk) s += 28
    if (hw.cameras.length > 0) s += 22
    if (hw.dualCameraLayout) s += 22
    else if (hw.cameras.length === 1) s += 8
    if (hw.previewing.length > 0) s += 14
    if (hw.recordingsApiOk) s += 14
    return Math.min(100, Math.round(s))
  }, [
    hw.arduinoOk,
    hw.cameras.length,
    hw.dualCameraLayout,
    hw.previewing.length,
    hw.recordingsApiOk,
  ])

  const cameraSystemOk = hw.cameras.length > 0
  const stimulusRows = useMemo(
    () =>
      [
        {
          id: 'light',
          label: 'Light',
          ready: hw.stimulusPathOk,
          testLabel: 'Test light',
          run: () => pulseIr(55),
        },
        {
          id: 'buzzer',
          label: 'Buzzer',
          ready: hw.stimulusPathOk,
          testLabel: 'Test sound',
          run: () => pulseBuzzer(48),
        },
        {
          id: 'vibration',
          label: 'Vibration',
          ready: hw.stimulusPathOk,
          testLabel: 'Test vibration',
          run: () => pulseVibration(42),
        },
        {
          id: 'water',
          label: 'Water flow',
          ready: hw.stimulusPathOk,
          testLabel: 'Test pump',
          run: () => pulsePump(38),
        },
      ] as const,
    [hw.stimulusPathOk],
  )

  async function runTest(id: string, fn: () => Promise<void>) {
    if (!hw.stimulusPathOk) {
      pushLog(`${id}: blocked — Arduino not connected`)
      return
    }
    setBusy(id)
    pushLog(`${id}: test started`)
    try {
      await fn()
      pushLog(`${id}: test finished OK`)
    } catch (e) {
      pushLog(`${id}: error — ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setBusy(null)
      void hw.refresh()
    }
  }

  async function runCameraTest(slotKey: string, name: string | null) {
    if (!name) {
      pushLog(`${slotKey}: no device assigned`)
      return
    }
    setBusy(`cam-${slotKey}`)
    pushLog(`Camera "${name}": preview test…`)
    try {
      await testCameraPreview(name)
      pushLog(`Camera "${name}": preview OK`)
    } catch (e) {
      pushLog(`Camera "${name}": ${e instanceof Error ? e.message : String(e)}`)
    } finally {
      setBusy(null)
      void hw.refresh()
    }
  }

  async function runFullDiagnostic() {
    if (!hw.stimulusPathOk && hw.cameras.length === 0) {
      pushLog('Diagnostic skipped — connect Arduino or attach a camera first')
      return
    }
    setBusy('full')
    pushLog('Full diagnostic started')
    await hw.refresh()
    try {
      for (const slot of hw.cameraSlots) {
        if (slot.cameraName) {
          pushLog(`Camera "${slot.cameraName}": preview…`)
          try {
            await testCameraPreview(slot.cameraName)
            pushLog(`Camera "${slot.cameraName}": OK`)
          } catch (e) {
            pushLog(`Camera "${slot.cameraName}": ${e instanceof Error ? e.message : String(e)}`)
          }
          await new Promise((r) => setTimeout(r, 400))
        }
      }
      if (hw.stimulusPathOk) {
        pushLog('Stimulus: IR pulse')
        await pulseIr(50)
        await new Promise((r) => setTimeout(r, 400))
        pushLog('Stimulus: buzzer')
        await pulseBuzzer(45)
        await new Promise((r) => setTimeout(r, 400))
        pushLog('Stimulus: vibration')
        await pulseVibration(40)
        await new Promise((r) => setTimeout(r, 400))
        pushLog('Stimulus: pump')
        await pulsePump(35)
      } else {
        pushLog('Stimulus tests skipped — Arduino offline')
      }
      pushLog('Full diagnostic finished')
    } finally {
      setBusy(null)
      void hw.refresh()
    }
  }

  return (
    <div className="mb-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-lg font-bold text-zimon-fg dark:text-cyan-50/95">Environment / System readiness</h1>
          <p className="mt-1 text-xs text-zimon-muted">Live status from the API — test actions hit real serial / camera endpoints.</p>
        </div>
        <span
          className={[
            'rounded-full border px-3 py-1 text-[10px] font-bold uppercase tracking-wide',
            hw.environmentOk
              ? 'border-emerald-500/40 text-emerald-400'
              : 'border-amber-500/40 text-amber-300',
          ].join(' ')}
        >
          {hw.environmentOk ? 'Operational' : 'Action required'}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Camera devices */}
        <section className="rounded-2xl border border-cyan-500/15 bg-slate-950/45 p-4 dark:border-cyan-500/20 dark:bg-slate-950/55">
          <div className="mb-3 flex items-center gap-2 border-b border-cyan-500/10 pb-2">
            <Video className="h-4 w-4 text-cyan-400" strokeWidth={2} />
            <h2 className="text-sm font-bold text-zimon-fg">Camera devices</h2>
          </div>
          <ul className="space-y-3">
            {hw.cameraSlots.map((slot) => {
              const connected = !!slot.cameraName
              const streaming = slot.streaming
              return (
                <li
                  key={slot.key}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zimon-border/50 bg-zimon-card/30 px-3 py-2.5 dark:border-cyan-500/10"
                >
                  <div className="min-w-0 flex items-center gap-2">
                    {connected ? (
                      <Check className="h-4 w-4 shrink-0 text-emerald-400" strokeWidth={2.5} />
                    ) : (
                      <span className="h-3 w-3 shrink-0 rounded-full bg-red-500" />
                    )}
                    <div className="min-w-0">
                      <div className="text-sm font-semibold text-zimon-fg">{slot.label}</div>
                      <div className="truncate text-[11px] text-zimon-muted">
                        {slot.cameraName ?? 'Not detected'}
                        {streaming ? ' · streaming' : connected ? ' · idle' : ''}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={[
                        'rounded-full px-2 py-0.5 text-[10px] font-bold uppercase',
                        connected
                          ? streaming
                            ? 'bg-sky-500/20 text-sky-300'
                            : 'bg-emerald-500/15 text-emerald-300'
                          : 'bg-red-500/15 text-red-300',
                      ].join(' ')}
                    >
                      {connected ? (streaming ? 'Live' : 'Connected') : 'Disconnected'}
                    </span>
                    <button
                      type="button"
                      disabled={!connected || busy !== null}
                      onClick={() => void runCameraTest(slot.key, slot.cameraName)}
                      className="inline-flex items-center gap-0.5 rounded-lg border border-cyan-500/30 px-2 py-1 text-[10px] font-bold text-cyan-200 transition-colors hover:bg-cyan-500/10 disabled:opacity-40"
                    >
                      Test
                      <ChevronRight className="h-3 w-3" />
                    </button>
                  </div>
                </li>
              )
            })}
          </ul>
          <div className="mt-4 flex items-center gap-2 border-t border-cyan-500/10 pt-3">
            <span className="text-xs font-semibold text-zimon-fg">System ready (cameras)</span>
            <Check
              className={cameraSystemOk ? 'h-4 w-4 text-emerald-400' : 'h-4 w-4 text-amber-400'}
              strokeWidth={2.5}
            />
            <div className="ml-auto h-2 min-w-[100px] flex-1 max-w-[200px] overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-gradient-to-r from-cyan-600 to-sky-500 transition-all duration-500"
                style={{ width: `${readinessPct}%` }}
              />
            </div>
            <span className="text-[10px] tabular-nums text-zimon-muted">{readinessPct}%</span>
          </div>
        </section>

        {/* Stimulus devices */}
        <section className="rounded-2xl border border-cyan-500/15 bg-slate-950/45 p-4 dark:border-cyan-500/20 dark:bg-slate-950/55">
          <div className="mb-3 flex items-center gap-2 border-b border-cyan-500/10 pb-2">
            <Lightbulb className="h-4 w-4 text-amber-300" strokeWidth={2} />
            <h2 className="text-sm font-bold text-zimon-fg">Stimulus devices</h2>
          </div>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {stimulusRows.map((row) => (
              <div
                key={row.id}
                className="flex items-center justify-between gap-2 rounded-xl border border-zimon-border/50 bg-zimon-card/30 px-3 py-2 dark:border-cyan-500/10"
              >
                <div className="flex min-w-0 items-center gap-2">
                  <input
                    type="checkbox"
                    readOnly
                    checked={row.ready}
                    className="pointer-events-none accent-emerald-500"
                    aria-hidden
                  />
                  <span className="text-sm font-medium text-zimon-fg">{row.label}</span>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span
                    className={row.ready ? 'text-[10px] font-semibold text-emerald-400' : 'text-[10px] text-red-400'}
                  >
                    {row.ready ? 'Ready' : 'Offline'}
                  </span>
                  <button
                    type="button"
                    disabled={busy !== null}
                    onClick={() => void runTest(row.id, row.run)}
                    className="rounded-lg bg-slate-800 px-2 py-1 text-[10px] font-semibold text-cyan-100 ring-1 ring-cyan-500/25 hover:bg-slate-700 disabled:opacity-40"
                  >
                    {busy === row.id ? <Loader2 className="h-3 w-3 animate-spin" /> : row.testLabel}
                  </button>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-4 flex items-center gap-2 border-t border-cyan-500/10 pt-3">
            <span className="text-xs font-semibold text-zimon-fg">System ready (stimuli)</span>
            <Check
              className={hw.stimulusPathOk ? 'h-4 w-4 text-emerald-400' : 'h-4 w-4 text-red-400'}
              strokeWidth={2.5}
            />
          </div>
        </section>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-cyan-500/15 bg-slate-950/40 p-4 dark:border-cyan-500/20">
        <div className="min-w-0">
          <p className={`text-sm font-medium ${hw.environmentOk ? 'text-emerald-300' : 'text-amber-200'}`}>
            {hw.environmentMessage}
          </p>
          <p className="mt-1 text-[11px] text-zimon-muted">
            Temperature:{' '}
            <span className="tabular-nums text-zimon-fg">
              {hw.temperatureC != null ? `${hw.temperatureC.toFixed(1)} °C` : '—'}
            </span>
            {' · '}
            Recordings API: {hw.recordingsApiOk ? 'reachable' : 'unavailable'}
          </p>
        </div>
        <button
          type="button"
          disabled={busy !== null}
          onClick={() => void runFullDiagnostic()}
          className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-sky-500 px-4 py-2.5 text-sm font-bold text-white shadow-md disabled:opacity-50"
        >
          {busy === 'full' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />}
          Run full diagnostic
        </button>
      </div>

      <div className="rounded-xl border border-zimon-border/60 bg-slate-950/40 p-3 dark:border-cyan-500/10">
        <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-zimon-muted">
          <Waves className="h-3.5 w-3.5" />
          Hardware event log
        </div>
        <ul className="mt-2 max-h-36 overflow-y-auto font-mono text-[10px] text-slate-400">
          {logLines.length === 0 ? <li>No tests yet — use Test buttons above.</li> : logLines.map((l, i) => <li key={i}>{l}</li>)}
        </ul>
      </div>
    </div>
  )
}
