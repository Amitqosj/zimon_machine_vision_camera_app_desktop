export type PhaseKind = 'baseline' | 'stimulus' | 'recovery'

export type StimulusType = 'light' | 'buzzer' | 'vibration' | 'water'

export interface StimulusConfig {
  type: StimulusType
  on: boolean
  intensity: number
  frequencyHz: number
  pulseWidthMs: number
  durationMs: number
  delayMs: number
  repetitions: number
}

export interface ProtocolPhase {
  id: string
  kind: PhaseKind
  durationS: number
  label?: string
  stimuli: StimulusConfig[]
}

export interface ZimonProtocol {
  id: string
  name: string
  description: string
  phases: ProtocolPhase[]
  updatedAt: string
}

export function newPhaseId(): string {
  return `ph-${crypto.randomUUID().slice(0, 8)}`
}

export function newProtocolId(): string {
  return `prot-${crypto.randomUUID().slice(0, 8)}`
}

export function defaultStimulus(type: StimulusType): StimulusConfig {
  return {
    type,
    on: false,
    intensity: 50,
    frequencyHz: 0,
    pulseWidthMs: 100,
    durationMs: 500,
    delayMs: 0,
    repetitions: 1,
  }
}
