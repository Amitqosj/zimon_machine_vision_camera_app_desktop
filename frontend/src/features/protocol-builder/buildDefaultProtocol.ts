import type { ProtocolPhase, ZimonProtocol } from '../../types/zimonProtocol'
import { defaultStimulus, newPhaseId, newProtocolId } from '../../types/zimonProtocol'

function phase(kind: ProtocolPhase['kind'], durationS: number, label: string): ProtocolPhase {
  return {
    id: newPhaseId(),
    kind,
    durationS,
    label,
    stimuli: [
      defaultStimulus('light'),
      defaultStimulus('buzzer'),
      defaultStimulus('vibration'),
      defaultStimulus('water'),
    ],
  }
}

export function buildDefaultProtocol(): ZimonProtocol {
  const now = new Date().toISOString()
  return {
    id: newProtocolId(),
    name: 'Untitled protocol',
    description: '',
    phases: [
      phase('baseline', 120, 'Baseline'),
      phase('stimulus', 60, 'Stimulus'),
      phase('recovery', 120, 'Recovery'),
    ],
    updatedAt: now,
  }
}
