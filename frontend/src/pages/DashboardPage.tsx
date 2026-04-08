import { Navigate } from 'react-router-dom'

/** Legacy route: bookmarks to `/app/dashboard` land on Adult execution. */
export function DashboardPage() {
  return <Navigate to="/app/adult" replace />
}
