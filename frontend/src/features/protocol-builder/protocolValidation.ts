import type { ZimonProtocol, ProtocolPhase } from '../../types/zimonProtocol'

export function validateProtocol(p: ZimonProtocol): string[] {
  const issues: string[] = []
  if (!p.name.trim()) issues.push('Protocol name is required.')
  if (p.phases.length === 0) issues.push('Add at least one phase.')

  let t = 0
  for (const ph of p.phases) {
    if (ph.durationS <= 0) issues.push(`Phase "${ph.label || ph.kind}" has invalid duration (must be > 0).`)
    for (const st of ph.stimuli) {
      if (st.on) {
        if (st.intensity < 0 || st.intensity > 100) {
          issues.push(`Stimulus ${st.type}: intensity must be 0–100.`)
        }
        if (st.durationMs < 0) issues.push(`Stimulus ${st.type}: duration cannot be negative.`)
        if (st.delayMs < 0) issues.push(`Stimulus ${st.type}: delay cannot be negative.`)
      }
    }
    t += ph.durationS
  }

  const overlaps = findOverlappingStimuli(p.phases)
  for (const o of overlaps) issues.push(o)

  if (t <= 0 && p.phases.length > 0) issues.push('Total protocol duration is zero.')
  return Array.from(new Set(issues))
}

function findOverlappingStimuli(phases: ProtocolPhase[]): string[] {
  const warnings: string[] = []
  for (const ph of phases) {
    const on = ph.stimuli.filter((s) => s.on)
    if (on.length > 1) {
      warnings.push(
        `Phase "${ph.label || ph.kind}": multiple stimuli enabled — verify hardware timing on device.`,
      )
    }
  }
  return warnings
}
