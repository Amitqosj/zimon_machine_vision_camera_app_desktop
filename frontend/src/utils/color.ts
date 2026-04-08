export function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const h = hex.replace('#', '')
  if (h.length !== 6) return { r: 0, g: 0, b: 0 }
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  }
}

function clampByte(n: number) {
  return Math.max(0, Math.min(255, Math.round(n)))
}

export function rgbToHex(r: number, g: number, b: number) {
  const x = (n: number) => clampByte(n).toString(16).padStart(2, '0')
  return `#${x(r)}${x(g)}${x(b)}`
}

/** Scale RGB luminance by factor 0–1 (for “intensity” on a chosen hue). */
export function scaleRgbHex(hex: string, intensity01: number) {
  const k = Math.max(0, Math.min(1, intensity01))
  const { r, g, b } = hexToRgb(hex)
  return rgbToHex(r * k, g * k, b * k)
}
