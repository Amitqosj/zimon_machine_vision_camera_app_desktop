import { Link } from 'react-router-dom'

/**
 * Camera / chamber calibration entry point.
 * Full calibration flows can be wired to the API here; this page keeps routing and builds working.
 */
export function CalibrationPage() {
  return (
    <div className="mx-auto w-full max-w-3xl space-y-4 pb-8">
      <div className="zimon-glass-panel rounded-2xl border border-zimon-border p-6">
        <h1 className="text-xl font-bold text-zimon-fg">Calibration</h1>
        <p className="mt-2 text-sm leading-relaxed text-zimon-muted">
          Use this area for camera and chamber calibration workflows. Hardware status is available from
          the Environment module while the API and devices are connected.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/app/environment"
            className="rounded-lg bg-gradient-to-r from-indigo-700 to-zimon-accent px-4 py-2 text-sm font-semibold text-white"
          >
            Open Environment
          </Link>
          <Link
            to="/app/adult"
            className="rounded-lg border border-zimon-border px-4 py-2 text-sm font-semibold text-zimon-fg"
          >
            Back to Adult
          </Link>
        </div>
      </div>
    </div>
  )
}
