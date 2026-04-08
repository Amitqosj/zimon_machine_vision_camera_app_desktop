import { hexToRgb, scaleRgbHex } from '../../utils/color'
import { mapToPwm } from '../../utils/pwm'

export type StimState = {
  enabled: boolean
  intensity: number
  durationMs: number
  delayMs: number
  continuous: boolean
}

export function defaultStim(): StimState {
  return {
    enabled: false,
    intensity: 0,
    durationMs: 0,
    delayMs: 0,
    continuous: false,
  }
}

export function buildStimuliPayload(
  vib: StimState,
  buzz: StimState,
  heat: StimState,
  rgbOn: boolean,
  rgbHex: string,
  rgbIntensityPct = 100,
): Record<string, Record<string, unknown>> {
  const out: Record<string, Record<string, unknown>> = {}
  if (vib.enabled) {
    out.VIB = {
      level: mapToPwm(vib.intensity),
      continuous: vib.continuous,
      duration_ms: vib.continuous ? 0 : vib.durationMs,
      delay_ms: vib.continuous ? 0 : vib.delayMs,
    }
  }
  if (buzz.enabled) {
    out.BUZZER = {
      level: mapToPwm(buzz.intensity),
      continuous: buzz.continuous,
      duration_ms: buzz.continuous ? 0 : buzz.durationMs,
      delay_ms: buzz.continuous ? 0 : buzz.delayMs,
    }
  }
  if (heat.enabled) {
    out.HEATER = {
      level: mapToPwm(heat.intensity),
      continuous: heat.continuous,
      duration_ms: heat.continuous ? 0 : heat.durationMs,
      delay_ms: heat.continuous ? 0 : heat.delayMs,
    }
  }
  if (rgbOn) {
    const scaled = scaleRgbHex(rgbHex, rgbIntensityPct / 100)
    const { r, g, b } = hexToRgb(scaled)
    out.RGB = { r, g, b, delay_ms: 0, duration_ms: 0 }
  }
  return out
}
