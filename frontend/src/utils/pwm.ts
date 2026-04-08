/** Match desktop `main_window._map_to_pwm`: 0–100 → 0–255 */
export function mapToPwm(value0to100: number): number {
  const v = Math.max(0, Math.min(100, value0to100))
  return Math.round((v / 100) * 255)
}
