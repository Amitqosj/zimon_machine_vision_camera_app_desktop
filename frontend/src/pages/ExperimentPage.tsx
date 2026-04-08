import { Navigate } from 'react-router-dom'

/** @deprecated Use `/app/experiments` — unified experiments hub. */
export function ExperimentPage() {
  return <Navigate to="/app/experiments" replace />
}
