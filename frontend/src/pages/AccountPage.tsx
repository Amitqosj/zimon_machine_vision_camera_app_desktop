import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiFetch } from '../api/client'
import { useAuth } from '../context/AuthContext'

type TabKey = 'profile' | 'session' | 'users'

type ManagedUser = {
  id: number
  full_name: string
  username: string
  email: string
  role: 'admin' | 'student'
  is_active: boolean
  is_locked: boolean
  created_at?: string | null
}

export function AccountPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [tab, setTab] = useState<TabKey>('profile')
  const [managedUsers, setManagedUsers] = useState<ManagedUser[]>([])
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [newStudent, setNewStudent] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
  })
  const [editDraft, setEditDraft] = useState<Record<number, { full_name: string; email: string; is_active: boolean }>>({})
  const [resetPasswords, setResetPasswords] = useState<Record<number, string>>({})

  const isAdmin = user?.role === 'admin'

  function initials() {
    const n = (user?.full_name || user?.username || '?').trim()
    const parts = n.split(/\s+/)
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
    return n.slice(0, 2).toUpperCase() || '—'
  }

  function doLogout() {
    if (!confirm('Logout and return to login?')) return
    logout()
    navigate('/login', { replace: true })
  }

  async function loadUsers() {
    if (!isAdmin) return
    setBusy(true)
    setError('')
    try {
      const users = await apiFetch<ManagedUser[]>('/api/users')
      setManagedUsers(users)
      const nextDraft: Record<number, { full_name: string; email: string; is_active: boolean }> = {}
      for (const u of users) {
        if (u.role !== 'student') continue
        nextDraft[u.id] = { full_name: u.full_name, email: u.email, is_active: u.is_active }
      }
      setEditDraft(nextDraft)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users')
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    void loadUsers()
  }, [isAdmin])

  async function createStudent(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setMessage('')
    setBusy(true)
    try {
      await apiFetch('/api/users', {
        method: 'POST',
        body: JSON.stringify(newStudent),
      })
      setMessage('Student created successfully.')
      setNewStudent({ full_name: '', username: '', email: '', password: '' })
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create student')
    } finally {
      setBusy(false)
    }
  }

  async function updateStudent(userId: number) {
    const draft = editDraft[userId]
    if (!draft) return
    setError('')
    setMessage('')
    setBusy(true)
    try {
      await apiFetch(`/api/users/${userId}`, {
        method: 'PUT',
        body: JSON.stringify(draft),
      })
      setMessage('Student updated successfully.')
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update student')
    } finally {
      setBusy(false)
    }
  }

  async function resetStudentPassword(userId: number) {
    const newPassword = (resetPasswords[userId] || '').trim()
    if (!newPassword) return
    setError('')
    setMessage('')
    setBusy(true)
    try {
      await apiFetch(`/api/users/${userId}/reset-password`, {
        method: 'POST',
        body: JSON.stringify({ new_password: newPassword }),
      })
      setResetPasswords((p) => ({ ...p, [userId]: '' }))
      setMessage('Student password reset successfully.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset password')
    } finally {
      setBusy(false)
    }
  }

  async function toggleLock(userId: number, shouldLock: boolean) {
    setError('')
    setMessage('')
    setBusy(true)
    try {
      await apiFetch(`/api/users/${userId}/${shouldLock ? 'lock' : 'unlock'}`, { method: 'POST' })
      setMessage(shouldLock ? 'Student locked.' : 'Student unlocked.')
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update lock status')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto w-full space-y-4 pb-8">
      <div className="rounded-2xl border border-zimon-border bg-zimon-panel overflow-hidden">
        <div className="flex border-b border-zimon-border">
          <button
            type="button"
            onClick={() => setTab('profile')}
            className={`flex-1 py-3 text-sm font-semibold ${
              tab === 'profile'
                ? 'bg-gradient-to-br from-zimon-accent to-zimon-accent2 text-white'
                : 'text-gray-500 hover:bg-white/5'
            }`}
          >
            Profile
          </button>
          <button
            type="button"
            onClick={() => setTab('session')}
            className={`flex-1 py-3 text-sm font-semibold ${
              tab === 'session'
                ? 'bg-gradient-to-br from-zimon-accent to-zimon-accent2 text-white'
                : 'text-gray-500 hover:bg-white/5'
            }`}
          >
            Session
          </button>
          {isAdmin ? (
            <button
              type="button"
              onClick={() => setTab('users')}
              className={`flex-1 py-3 text-sm font-semibold ${
                tab === 'users'
                  ? 'bg-gradient-to-br from-zimon-accent to-zimon-accent2 text-white'
                  : 'text-gray-500 hover:bg-white/5'
              }`}
            >
              User Management
            </button>
          ) : null}
        </div>

        {tab === 'profile' ? (
          <div className="p-6 space-y-6">
            <div className="flex gap-5 items-start rounded-2xl border border-zimon-border bg-gradient-to-br from-[#16181f] to-[#101218] p-6">
              <div className="w-20 h-20 shrink-0 rounded-full bg-gradient-to-br from-zimon-accent to-zimon-accent2 flex items-center justify-center text-2xl font-bold text-white border-2 border-white/20">
                {initials()}
              </div>
              <div className="min-w-0">
                <div className="text-xl font-bold text-white">
                  {user?.full_name || 'Guest user'}
                </div>
                <div className="text-indigo-300 text-sm font-semibold">
                  @{user?.username || '—'}
                </div>
                <div className="mt-2 inline-block text-[11px] font-bold tracking-wider px-3 py-1 rounded-full border border-indigo-500/45 bg-indigo-500/20 text-indigo-200">
                  {(user?.role || 'student').toUpperCase()}
                </div>
              </div>
            </div>
            <div className="rounded-xl border border-zimon-border bg-zimon-card p-5 space-y-3 text-sm">
              <div className="text-xs font-bold tracking-widest text-gray-500">ACCOUNT DETAILS</div>
              <div className="flex justify-between border-b border-zimon-border/50 py-2">
                <span className="text-gray-500">Email</span>
                <span className="text-white">{user?.email || '—'}</span>
              </div>
              <div className="flex justify-between border-b border-zimon-border/50 py-2">
                <span className="text-gray-500">Username</span>
                <span className="text-white">{user?.username || '—'}</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-gray-500">Member since</span>
                <span className="text-white">{user?.created_at || '—'}</span>
              </div>
            </div>
          </div>
        ) : tab === 'session' ? (
          <div className="p-6">
            <div className="rounded-xl border border-zimon-border bg-zimon-card p-6 space-y-3">
              <div className="text-white font-bold">Session</div>
              <p className="text-sm text-gray-500 leading-relaxed">
                Sign out to return to the login screen. Unsaved work in this session may be lost.
              </p>
              <button
                type="button"
                onClick={doLogout}
                className="mt-2 w-full rounded-lg bg-gradient-to-r from-indigo-700 to-zimon-accent py-3 font-semibold text-white"
              >
                Log out
              </button>
            </div>
          </div>
        ) : (
          <div className="p-6 space-y-6">
            {message ? <div className="rounded-lg bg-emerald-500/15 px-3 py-2 text-sm text-emerald-300">{message}</div> : null}
            {error ? <div className="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-300">{error}</div> : null}

            <form onSubmit={createStudent} className="rounded-xl border border-zimon-border bg-zimon-card p-4 space-y-3">
              <div className="text-white font-semibold">Add Student</div>
              <input
                className="w-full rounded-md bg-slate-900/60 border border-zimon-border px-3 py-2 text-sm text-white"
                placeholder="Full name"
                value={newStudent.full_name}
                onChange={(e) => setNewStudent((p) => ({ ...p, full_name: e.target.value }))}
                required
              />
              <input
                className="w-full rounded-md bg-slate-900/60 border border-zimon-border px-3 py-2 text-sm text-white"
                placeholder="Username"
                value={newStudent.username}
                onChange={(e) => setNewStudent((p) => ({ ...p, username: e.target.value }))}
                required
              />
              <input
                className="w-full rounded-md bg-slate-900/60 border border-zimon-border px-3 py-2 text-sm text-white"
                placeholder="Email"
                type="email"
                value={newStudent.email}
                onChange={(e) => setNewStudent((p) => ({ ...p, email: e.target.value }))}
                required
              />
              <input
                className="w-full rounded-md bg-slate-900/60 border border-zimon-border px-3 py-2 text-sm text-white"
                placeholder="Password"
                type="password"
                value={newStudent.password}
                onChange={(e) => setNewStudent((p) => ({ ...p, password: e.target.value }))}
                required
                minLength={6}
              />
              <div className="text-xs text-gray-400">Role is always assigned as STUDENT.</div>
              <button type="submit" disabled={busy} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white">
                Create student
              </button>
            </form>

            <div className="space-y-3">
              {managedUsers
                .filter((u) => u.role === 'student')
                .map((u) => (
                  <div key={u.id} className="rounded-xl border border-zimon-border bg-zimon-card p-4 space-y-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <div className="text-white font-semibold">{u.full_name}</div>
                        <div className="text-xs text-gray-400">@{u.username} • {u.email}</div>
                      </div>
                      <div className="text-xs text-gray-400">
                        {u.is_active ? 'Active' : 'Inactive'} / {u.is_locked ? 'Locked' : 'Unlocked'}
                      </div>
                    </div>
                    <input
                      className="w-full rounded-md bg-slate-900/60 border border-zimon-border px-3 py-2 text-sm text-white"
                      value={editDraft[u.id]?.full_name || ''}
                      onChange={(e) =>
                        setEditDraft((p) => ({ ...p, [u.id]: { ...(p[u.id] || { full_name: '', email: '', is_active: true }), full_name: e.target.value } }))
                      }
                    />
                    <input
                      className="w-full rounded-md bg-slate-900/60 border border-zimon-border px-3 py-2 text-sm text-white"
                      type="email"
                      value={editDraft[u.id]?.email || ''}
                      onChange={(e) =>
                        setEditDraft((p) => ({ ...p, [u.id]: { ...(p[u.id] || { full_name: '', email: '', is_active: true }), email: e.target.value } }))
                      }
                    />
                    <label className="flex items-center gap-2 text-sm text-gray-300">
                      <input
                        type="checkbox"
                        checked={editDraft[u.id]?.is_active ?? true}
                        onChange={(e) =>
                          setEditDraft((p) => ({ ...p, [u.id]: { ...(p[u.id] || { full_name: '', email: '', is_active: true }), is_active: e.target.checked } }))
                        }
                      />
                      Active account
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <button type="button" disabled={busy} onClick={() => void updateStudent(u.id)} className="rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white">
                        Save
                      </button>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void toggleLock(u.id, !u.is_locked)}
                        className="rounded-lg bg-amber-600 px-3 py-2 text-xs font-semibold text-white"
                      >
                        {u.is_locked ? 'Unlock' : 'Lock'}
                      </button>
                    </div>
                    <div className="flex gap-2">
                      <input
                        className="flex-1 rounded-md bg-slate-900/60 border border-zimon-border px-3 py-2 text-sm text-white"
                        placeholder="New password"
                        type="password"
                        minLength={6}
                        value={resetPasswords[u.id] || ''}
                        onChange={(e) => setResetPasswords((p) => ({ ...p, [u.id]: e.target.value }))}
                      />
                      <button type="button" disabled={busy} onClick={() => void resetStudentPassword(u.id)} className="rounded-lg bg-rose-600 px-3 py-2 text-xs font-semibold text-white">
                        Reset Password
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
