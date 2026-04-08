import { apiFetch } from '../api/client'
import { mapToPwm } from './pwm'

export async function pulseIr(intensityPct = 50): Promise<void> {
  const pwm = mapToPwm(intensityPct)
  await apiFetch('/api/arduino/command', {
    method: 'POST',
    body: JSON.stringify({ command: `IR ${pwm}` }),
  })
  await new Promise((r) => setTimeout(r, 200))
  await apiFetch('/api/arduino/command', {
    method: 'POST',
    body: JSON.stringify({ command: 'IR 0' }),
  })
}

export async function pulseWhite(intensityPct = 50): Promise<void> {
  const pwm = mapToPwm(intensityPct)
  await apiFetch('/api/arduino/command', {
    method: 'POST',
    body: JSON.stringify({ command: `WHITE ${pwm}` }),
  })
  await new Promise((r) => setTimeout(r, 200))
  await apiFetch('/api/arduino/command', {
    method: 'POST',
    body: JSON.stringify({ command: 'WHITE 0' }),
  })
}

export async function pulseBuzzer(intensityPct = 45): Promise<void> {
  const pwm = mapToPwm(intensityPct)
  await apiFetch('/api/arduino/command', {
    method: 'POST',
    body: JSON.stringify({ command: `BUZZER ${pwm}` }),
  })
  await new Promise((r) => setTimeout(r, 220))
  await apiFetch('/api/arduino/command', {
    method: 'POST',
    body: JSON.stringify({ command: 'BUZZER 0' }),
  })
}

export async function pulseVibration(intensityPct = 40): Promise<void> {
  const pwm = mapToPwm(intensityPct)
  await apiFetch('/api/arduino/command', {
    method: 'POST',
    body: JSON.stringify({ command: `VIB ${pwm}` }),
  })
  await new Promise((r) => setTimeout(r, 220))
  await apiFetch('/api/arduino/command', {
    method: 'POST',
    body: JSON.stringify({ command: 'VIB 0' }),
  })
}

export async function pulsePump(intensityPct = 35): Promise<void> {
  const pwm = mapToPwm(intensityPct)
  await apiFetch('/api/arduino/command', {
    method: 'POST',
    body: JSON.stringify({ command: `PUMP ${pwm}` }),
  })
  await new Promise((r) => setTimeout(r, 350))
  await apiFetch('/api/arduino/command', {
    method: 'POST',
    body: JSON.stringify({ command: 'PUMP 0' }),
  })
}

/** Brief preview on a named camera (does not leave preview running). */
export async function testCameraPreview(cameraName: string, holdMs = 2800): Promise<void> {
  const enc = encodeURIComponent(cameraName)
  await apiFetch(`/api/camera/preview/start?camera_name=${enc}`, { method: 'POST' })
  await new Promise((r) => setTimeout(r, holdMs))
  await apiFetch(`/api/camera/preview/stop?camera_name=${enc}`, { method: 'POST' })
}
