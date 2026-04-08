import { ArrowRight, Eye, EyeOff, Lock, User } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiFetch } from '../api/client'
import { AuthPremiumShell } from '../components/auth/AuthPremiumShell'
import { AuthStatusBar } from '../components/auth/AuthStatusBar'
import { AuthTextField } from '../components/auth/AuthTextField'
import { PremiumBrandPanel } from '../components/auth/PremiumBrandPanel'
import { useAuth } from '../context/AuthContext'

const REMEMBER_KEY = 'zimon_remember_username'
const USERNAME_KEY = 'zimon_saved_username'

export function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [usernameOrEmail, setUsernameOrEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [remember, setRemember] = useState(false)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    try {
      const r = localStorage.getItem(REMEMBER_KEY) === '1'
      const u = localStorage.getItem(USERNAME_KEY) || ''
      setRemember(r)
      if (r && u) setUsernameOrEmail(u)
    } catch {
      /* ignore */
    }
  }, [])

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const res = await apiFetch<{ access_token: string }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({
          username_or_email: usernameOrEmail,
          password,
        }),
      })
      try {
        if (remember) {
          localStorage.setItem(REMEMBER_KEY, '1')
          localStorage.setItem(USERNAME_KEY, usernameOrEmail)
        } else {
          localStorage.removeItem(REMEMBER_KEY)
          localStorage.removeItem(USERNAME_KEY)
        }
      } catch {
        /* ignore */
      }
      await login(res.access_token)
      navigate('/app/adult', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthPremiumShell
      brand={<PremiumBrandPanel />}
      footer={<AuthStatusBar mode="login-card" />}
    >
      <div className="flex flex-1 flex-col justify-center px-6 py-10 sm:px-10 sm:py-12 lg:px-12 xl:px-14">
        <div className="mx-auto w-full max-w-[400px]">
          <h2 className="text-3xl font-bold tracking-tight text-[#0a192f] sm:text-[2rem] sm:leading-tight">
            Welcome to ZIMON
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Zebrafish Integrated Motion &amp; Optical Neuroanalysis Chamber
          </p>

          <form onSubmit={onSubmit} className="mt-9 space-y-5 sm:mt-10 sm:space-y-6">
            {error ? (
              <div
                role="alert"
                className="rounded-xl border border-red-200/80 bg-red-50 px-4 py-3 text-sm text-red-800 shadow-sm"
              >
                {error}
              </div>
            ) : null}

            <AuthTextField
              id="login-user"
              label="Email or Username"
              leftIcon={User}
              autoComplete="username"
              placeholder="Enter your email or username"
              value={usernameOrEmail}
              onChange={(e) => setUsernameOrEmail(e.target.value)}
            />

            <AuthTextField
              id="login-pass"
              label="Password"
              leftIcon={Lock}
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              rightSlot={
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <EyeOff className="h-[1.125rem] w-[1.125rem]" />
                  ) : (
                    <Eye className="h-[1.125rem] w-[1.125rem]" />
                  )}
                </button>
              }
            />

            <div className="flex flex-wrap items-center justify-between gap-3 pt-0.5">
              <label className="flex cursor-pointer select-none items-center gap-2.5 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-[#1e3a5f] focus:ring-[#1e3a5f]"
                />
                Remember me
              </label>
              <Link
                to="/forgot-password"
                className="text-sm font-semibold text-[#1e3a5f] underline-offset-2 transition hover:text-[#152a45] hover:underline"
              >
                Forgot Password?
              </Link>
            </div>

            <button
              type="submit"
              disabled={busy}
              className="group mt-1 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#1e3a5f] via-[#1a3254] to-[#152a45] py-3.5 text-base font-semibold text-white shadow-lg shadow-blue-950/25 transition hover:shadow-xl hover:shadow-blue-950/30 hover:brightness-[1.03] active:scale-[0.99] disabled:pointer-events-none disabled:opacity-55"
            >
              {busy ? 'Signing in…' : 'Login'}
              {!busy ? (
                <ArrowRight
                  className="h-5 w-5 transition-transform group-hover:translate-x-0.5"
                  aria-hidden
                />
              ) : null}
            </button>

          </form>
        </div>
      </div>
    </AuthPremiumShell>
  )
}
