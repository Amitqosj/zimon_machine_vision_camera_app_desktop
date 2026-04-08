import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { apiFetch } from '../api/client'

export type CameraRoleSlot = {
  key: string
  label: string
  cameraName: string | null
  streaming: boolean
}

function assignCameraRoles(cameras: string[], previewing: string[]): CameraRoleSlot[] {
  const c0 = cameras[0] ?? null
  const c1 = cameras[1] ?? null
  const larval =
    cameras.find((c) => /larval|machine|integrated|well/i.test(c)) ?? c0
  const bySide = cameras.find((c) => /side/i.test(c))
  const byTop = cameras.find((c) => /top|primary/i.test(c) && !/side/i.test(c))
  const adultTop = byTop ?? c0
  let adultSide = bySide ?? null
  if (!adultSide && c1 && c1 !== adultTop) adultSide = c1
  const pv = new Set(previewing)
  return [
    {
      key: 'larval',
      label: 'Machine vision (Larval)',
      cameraName: larval,
      streaming: !!(larval && pv.has(larval)),
    },
    {
      key: 'adultTop',
      label: 'USB camera (Adult top)',
      cameraName: adultTop,
      streaming: !!(adultTop && pv.has(adultTop)),
    },
    {
      key: 'adultSide',
      label: 'USB camera (Adult side)',
      cameraName: adultSide,
      streaming: !!(adultSide && pv.has(adultSide)),
    },
  ]
}

type Ctx = {
  arduinoOk: boolean
  cameras: string[]
  previewing: string[]
  expRunning: boolean
  temperatureC: number | null
  recordingsApiOk: boolean
  cameraSlots: CameraRoleSlot[]
  /** Arduino + at least one camera enumerated (minimal run). */
  readyForExperiment: boolean
  /** Two distinct cameras available (adult top + side style). */
  dualCameraLayout: boolean
  /** Stimulus path available. */
  stimulusPathOk: boolean
  /** Honest aggregate for UI copy — not “all OK” if side cam missing. */
  environmentMessage: string
  environmentOk: boolean
  refresh: () => Promise<void>
}

const HardwareStatusContext = createContext<Ctx | null>(null)

export function HardwareStatusProvider({ children }: { children: ReactNode }) {
  const [arduinoOk, setArduinoOk] = useState(false)
  const [cameras, setCameras] = useState<string[]>([])
  const [previewing, setPreviewing] = useState<string[]>([])
  const [expRunning, setExpRunning] = useState(false)
  const [temperatureC, setTemperatureC] = useState<number | null>(null)
  const [recordingsApiOk, setRecordingsApiOk] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const a = await apiFetch<{ connected: boolean }>('/api/arduino/status')
      setArduinoOk(!!a.connected)
    } catch {
      setArduinoOk(false)
    }
    try {
      await apiFetch('/api/camera/refresh', { method: 'POST' })
      const r = await apiFetch<{ cameras: string[] }>('/api/camera/list')
      setCameras(r.cameras ?? [])
    } catch {
      setCameras([])
    }
    try {
      const p = await apiFetch<{ previewing: string[] }>('/api/camera/preview/status')
      setPreviewing(p.previewing ?? [])
    } catch {
      setPreviewing([])
    }
    try {
      const e = await apiFetch<{ running: boolean }>('/api/experiment/status')
      setExpRunning(!!e.running)
    } catch {
      setExpRunning(false)
    }
    try {
      const t = await apiFetch<{ celsius: number | null }>('/api/arduino/temperature')
      setTemperatureC(t.celsius ?? null)
    } catch {
      setTemperatureC(null)
    }
    try {
      await apiFetch('/api/recordings/list')
      setRecordingsApiOk(true)
    } catch {
      setRecordingsApiOk(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
    const id = window.setInterval(() => void refresh(), 3000)
    return () => window.clearInterval(id)
  }, [refresh])

  const cameraSlots = useMemo(
    () => assignCameraRoles(cameras, previewing),
    [cameras, previewing],
  )

  const dualCameraLayout = useMemo(() => {
    const names = new Set(cameraSlots.map((s) => s.cameraName).filter(Boolean) as string[])
    return names.size >= 2
  }, [cameraSlots])

  const readyForExperiment = arduinoOk && cameras.length > 0
  const stimulusPathOk = arduinoOk

  const { environmentMessage, environmentOk } = useMemo(() => {
    const parts: string[] = []
    if (!arduinoOk) parts.push('Arduino disconnected — connect serial in Settings.')
    if (cameras.length === 0) parts.push('No cameras detected — check USB / API camera stack.')
    const side = cameraSlots.find((s) => s.key === 'adultSide')
    if (cameras.length === 1 && side && !side.cameraName) {
      parts.push('Adult side camera not assigned (only one device).')
    }
    if (parts.length === 0) {
      return {
        environmentMessage: 'Hardware link OK. You can run experiments or test protocols.',
        environmentOk: true,
      }
    }
    return { environmentMessage: parts.join(' '), environmentOk: false }
  }, [arduinoOk, cameras.length, cameraSlots])

  const value = useMemo(
    () => ({
      arduinoOk,
      cameras,
      previewing,
      expRunning,
      temperatureC,
      recordingsApiOk,
      cameraSlots,
      readyForExperiment,
      dualCameraLayout,
      stimulusPathOk,
      environmentMessage,
      environmentOk,
      refresh,
    }),
    [
      arduinoOk,
      cameras,
      previewing,
      expRunning,
      temperatureC,
      recordingsApiOk,
      cameraSlots,
      readyForExperiment,
      dualCameraLayout,
      stimulusPathOk,
      environmentMessage,
      environmentOk,
      refresh,
    ],
  )

  return <HardwareStatusContext.Provider value={value}>{children}</HardwareStatusContext.Provider>
}

export function useHardwareStatus() {
  const c = useContext(HardwareStatusContext)
  if (!c) throw new Error('useHardwareStatus must be used within HardwareStatusProvider')
  return c
}
