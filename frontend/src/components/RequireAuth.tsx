import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function RequireAuth() {
  const { user, loading } = useAuth()
  const loc = useLocation()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-zimon-bg text-gray-400">
        Loading session…
      </div>
    )
  }
  if (!user) {
    return <Navigate to="/login" state={{ from: loc }} replace />
  }
  return <Outlet />
}
