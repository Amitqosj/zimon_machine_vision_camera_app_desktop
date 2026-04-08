import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../../../api/client'

type TempRes = { celsius: number | null }

export function useDashboardArduino() {
  const [arduinoOk, setArduinoOk] = useState(false)
  const [port, setPort] = useState<string | null>(null)
  const [temp, setTemp] = useState<number | null>(null)
  const [pumpLevel, setPumpLevel] = useState(0)

  const pollStatus = useCallback(async () => {
    try {
      const s = await apiFetch<{ connected: boolean; port: string | null }>(
        '/api/arduino/status',
      )
      setArduinoOk(s.connected)
      setPort(s.port)
    } catch {
      setArduinoOk(false)
      setPort(null)
    }
  }, [])

  useEffect(() => {
    void pollStatus()
    const id = window.setInterval(() => void pollStatus(), 3000)
    return () => window.clearInterval(id)
  }, [pollStatus])

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

  const sendCmd = useCallback(async (cmd: string) => {
    try {
      await apiFetch('/api/arduino/command', {
        method: 'POST',
        body: JSON.stringify({ command: cmd }),
      })
    } catch {
      /* ignore */
    }
  }, [])

  return {
    arduinoOk,
    port,
    temp,
    pumpLevel,
    setPumpLevel,
    sendCmd,
    pollStatus,
  }
}
