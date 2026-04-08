import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../../../api/client'
import { buildStimuliPayload, defaultStim, type StimState } from '../experimentPayload'

export function useDashboardExperiment(cam: string) {
  const [running, setRunning] = useState(false)
  const [durationS, setDurationS] = useState(300)
  const [timerLabel, setTimerLabel] = useState('00:00:00')
  const [elapsedRatio, setElapsedRatio] = useState(0)
  const [startTs, setStartTs] = useState<number | null>(null)
  const [vib, setVib] = useState<StimState>(defaultStim)
  const [buzz, setBuzz] = useState<StimState>(defaultStim)
  const [heat, setHeat] = useState<StimState>(defaultStim)
  const [rgbOn, setRgbOn] = useState(false)
  const [rgbHex, setRgbHex] = useState('#ffffff')
  const [rgbIntensityPct, setRgbIntensityPct] = useState(80)
  const [activeList, setActiveList] = useState('None')
  const [err, setErr] = useState('')

  const setVibP = (u: Partial<StimState>) => setVib((p) => ({ ...p, ...u }))
  const setBuzzP = (u: Partial<StimState>) => setBuzz((p) => ({ ...p, ...u }))
  const setHeatP = (u: Partial<StimState>) => setHeat((p) => ({ ...p, ...u }))

  const pollStatus = useCallback(async () => {
    try {
      const s = await apiFetch<{ running: boolean }>('/api/experiment/status')
      setRunning(s.running)
      if (!s.running) {
        setStartTs(null)
        setTimerLabel('00:00:00')
        setElapsedRatio(0)
      }
    } catch {
      setRunning(false)
    }
  }, [])

  useEffect(() => {
    void pollStatus()
    const id = window.setInterval(() => void pollStatus(), 1500)
    return () => window.clearInterval(id)
  }, [pollStatus])

  useEffect(() => {
    if (!startTs || !running) return
    const cap = durationS > 0 ? durationS : 1
    const id = window.setInterval(() => {
      const elapsed = (Date.now() - startTs) / 1000
      const h = Math.floor(elapsed / 3600)
      const m = Math.floor((elapsed % 3600) / 60)
      const sec = Math.floor(elapsed % 60)
      setTimerLabel(
        `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`,
      )
      setElapsedRatio(Math.min(1, elapsed / cap))
    }, 500)
    return () => window.clearInterval(id)
  }, [startTs, running, durationS])

  const sendVib = (pwm: number) => {
    void apiFetch('/api/arduino/command', {
      method: 'POST',
      body: JSON.stringify({ command: `VIB ${pwm}` }),
    }).catch(() => {})
  }

  const sendBuzz = (pwm: number) => {
    void apiFetch('/api/arduino/command', {
      method: 'POST',
      body: JSON.stringify({ command: `BUZZER ${pwm}` }),
    }).catch(() => {})
  }

  async function startExperiment(plateWells: number, camerasOverride?: string[]) {
    setErr('')
    const stimuli = buildStimuliPayload(
      vib,
      buzz,
      heat,
      rgbOn,
      rgbHex,
      rgbIntensityPct,
    )
    const keys = Object.keys(stimuli)
    setActiveList(keys.length ? keys.join(', ') : 'None')
    const dur =
      durationS > 0 ? durationS : keys.length > 0 ? 300 : 60
    const prefix = `exp_w${plateWells}`
    const camera_list =
      camerasOverride && camerasOverride.length > 0
        ? Array.from(new Set(camerasOverride.filter(Boolean)))
        : cam
          ? [cam]
          : []
    try {
      await apiFetch('/api/experiment/start', {
        method: 'POST',
        body: JSON.stringify({
          duration_s: dur,
          filename_prefix: prefix,
          camera_list,
          stimuli,
        }),
      })
      setRunning(true)
      setStartTs(Date.now())
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function stopExperiment() {
    setErr('')
    try {
      await apiFetch('/api/experiment/stop', { method: 'POST' })
      setRunning(false)
      setStartTs(null)
      setTimerLabel('00:00:00')
      setElapsedRatio(0)
      setActiveList('None')
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  return {
    running,
    startTs,
    durationS,
    setDurationS,
    timerLabel,
    elapsedRatio,
    vib,
    buzz,
    heat,
    rgbOn,
    setRgbOn,
    rgbHex,
    setRgbHex,
    rgbIntensityPct,
    setRgbIntensityPct,
    setVibP,
    setBuzzP,
    setHeatP,
    activeList,
    err,
    setErr,
    startExperiment,
    stopExperiment,
    sendVib,
    sendBuzz,
  }
}
