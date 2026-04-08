import { ArrowLeft, User } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '../api/client'
import { AuthPremiumShell } from '../components/auth/AuthPremiumShell'
import { AuthTextField } from '../components/auth/AuthTextField'
import { PremiumBrandPanel } from '../components/auth/PremiumBrandPanel'

export function ForgotPasswordPage() {
  const [usernameOrEmail, setUsernameOrEmail] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  const [serverMessage, setServerMessage] = useState('')

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const res = await apiFetch<{ message: string }>('/api/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ username_or_email: usernameOrEmail }),
      })
      setServerMessage(res.message)
      setDone(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthPremiumShell brand={<PremiumBrandPanel />}>
      <div className="flex flex-1 flex-col justify-center px-6 py-10 sm:px-10 sm:py-12 lg:px-12 xl:px-14">
        <div className="mx-auto w-full max-w-[400px]">
          <h2 className="text-3xl font-bold tracking-tight text-[#0a192f] sm:text-[2rem] sm:leading-tight">
            Forgot password?
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Enter the email or username associated with your ZIMON account. Recovery is handled by
            your system administrator.
          </p>

          {done ? (
            <div className="mt-9 space-y-6 sm:mt-10">
              <div
                role="status"
                className="rounded-xl border border-emerald-200/80 bg-emerald-50/90 px-4 py-4 text-sm leading-relaxed text-emerald-950 shadow-sm"
              >
                {serverMessage}
              </div>
              <Link
                to="/login"
                className="group flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#1e3a5f] via-[#1a3254] to-[#152a45] py-3.5 text-base font-semibold text-white shadow-lg shadow-blue-950/25 transition hover:shadow-xl hover:shadow-blue-950/30 hover:brightness-[1.03] active:scale-[0.99]"
              >
                <ArrowLeft
                  className="h-5 w-5 transition-transform group-hover:-translate-x-0.5"
                  aria-hidden
                />
                Back to sign in
              </Link>
            </div>
          ) : (
            <form onSubmit={onSubmit} className="mt-9 space-y-6 sm:mt-10">
              {error ? (
                <div
                  role="alert"
                  className="rounded-xl border border-red-200/80 bg-red-50 px-4 py-3 text-sm text-red-800 shadow-sm"
                >
                  {error}
                </div>
              ) : null}

              <AuthTextField
                id="forgot-user"
                label="Email or Username"
                leftIcon={User}
                autoComplete="username"
                placeholder="Enter your email or username"
                value={usernameOrEmail}
                onChange={(e) => setUsernameOrEmail(e.target.value)}
                required
              />

              <button
                type="submit"
                disabled={busy}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#1e3a5f] via-[#1a3254] to-[#152a45] py-3.5 text-base font-semibold text-white shadow-lg shadow-blue-950/25 transition hover:shadow-xl hover:shadow-blue-950/30 hover:brightness-[1.03] active:scale-[0.99] disabled:pointer-events-none disabled:opacity-55"
              >
                {busy ? 'Submitting…' : 'Submit recovery request'}
              </button>

              <Link
                to="/login"
                className="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-[#1e3a5f] bg-white py-3.5 text-base font-semibold text-[#1e3a5f] shadow-sm transition hover:border-[#152a45] hover:bg-slate-50 hover:shadow-md active:scale-[0.99]"
              >
                <ArrowLeft className="h-5 w-5" aria-hidden />
                Back to sign in
              </Link>
            </form>
          )}

        </div>
      </div>
    </AuthPremiumShell>
  )
}
