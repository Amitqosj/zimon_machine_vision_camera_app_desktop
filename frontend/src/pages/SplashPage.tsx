import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AuthStatusBar } from '../components/auth/AuthStatusBar'
import { ZIMON_LOGO_URL } from '../constants/branding'
import { useAuth } from '../context/AuthContext'

export function SplashPage() {
  const navigate = useNavigate()
  const { user, loading } = useAuth()

  useEffect(() => {
    if (loading) return
    const t = window.setTimeout(() => {
      navigate(user ? '/app/adult' : '/login', { replace: true })
    }, 700)
    return () => window.clearTimeout(t)
  }, [loading, user, navigate])

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center gap-4 bg-zimon-bg px-4 pb-28">
      <div className="h-20 w-20 overflow-hidden rounded-full border border-cyan-400/25 bg-slate-950/50 shadow-lg shadow-cyan-500/15 ring-2 ring-cyan-400/10">
        <img src={ZIMON_LOGO_URL} alt="" width={80} height={80} className="h-full w-full object-cover" decoding="async" />
      </div>
      <div className="text-xl font-bold tracking-[0.2em] text-zimon-fg">ZIMON</div>
      <div className="text-sm text-zimon-muted">Behaviour Tracking System</div>
      <div className="mt-6 h-1 w-32 rounded-full bg-gradient-to-r from-zimon-accent to-zimon-accent2 animate-pulse" />
      <AuthStatusBar mode="splash-dock" />
    </div>
  )
}
