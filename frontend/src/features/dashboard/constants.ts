export type AssayDef = {
  id: string
  icon: string
  title: string
  description: string
}

export const ASSAYS: AssayDef[] = [
  {
    id: 'multi-well',
    icon: '▦',
    title: 'Multi-Well Plate',
    description: 'Assess decision making and spatial preference.',
  },
  {
    id: 'larval-maze',
    icon: '◇',
    title: 'Larval Reservoir Maze',
    description: 'Track navigation and memory in structured paths.',
  },
  {
    id: 't-maze',
    icon: '⊤',
    title: 'Alternating T Maze',
    description: 'Measure turning bias and exploration.',
  },
  {
    id: 'open-field',
    icon: '▢',
    title: 'Open Field Arena',
    description: 'General locomotion and anxiety-related movement.',
  },
  {
    id: 'ld-choice',
    icon: '◐',
    title: 'L/D Choice Assay',
    description: 'Light vs dark preference and phototaxis.',
  },
]

export type PlateDef = { wells: 12 | 24 | 48 | 96; label: string }

export const PLATES: PlateDef[] = [
  { wells: 12, label: '12 Well Plate' },
  { wells: 24, label: '24 Well Plate' },
  { wells: 48, label: '48 Well Plate' },
  { wells: 96, label: '96 Well Plate' },
]

export type RecipeDef = {
  id: string
  title: string
  blurb: string
  tip: string
  durationS: number
  fps: number
  rgbPct?: number
}

export const RECIPES: RecipeDef[] = [
  {
    id: 'custom',
    title: 'Custom Assay',
    blurb: 'User-defined timing and stimuli.',
    tip: "For Custom Assay, set RGB to ~80% intensity, 60 FPS, and ~20 min duration when the chamber allows it.",
    durationS: 1200,
    fps: 60,
    rgbPct: 80,
  },
  {
    id: 'larval-loco',
    title: 'Larval Locomotion',
    blurb: 'Standard locomotion capture for larvae.',
    tip: 'Use moderate white light and stable temperature; avoid sudden vibration.',
    durationS: 600,
    fps: 30,
  },
  {
    id: 'anxiety',
    title: 'Anxiety Test',
    blurb: 'Open-field style with minimal disturbance.',
    tip: 'Start with IR-only illumination; keep buzzer off until protocol demands it.',
    durationS: 900,
    fps: 30,
  },
  {
    id: 'predator',
    title: 'Predator Exposure',
    blurb: 'Controlled stimulus timing for avoidance.',
    tip: 'Preflight pumps and vibration; confirm water flow before recording.',
    durationS: 480,
    fps: 60,
  },
]
