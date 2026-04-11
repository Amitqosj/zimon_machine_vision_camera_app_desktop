const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8010'

const TOKEN_KEY = 'zimon_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export function apiUrl(path: string): string {
  if (path.startsWith('http')) return path
  const base = API_BASE.replace(/\/$/, '')
  const p = path.startsWith('/') ? path : `/${path}`
  return `${base}${p}`
}

export async function apiFetch<T = unknown>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers)
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (
    init.body &&
    typeof init.body === 'string' &&
    !headers.has('Content-Type')
  ) {
    headers.set('Content-Type', 'application/json')
  }
  const res = await fetch(apiUrl(path), { ...init, headers })
  const text = await res.text()
  if (!res.ok) {
    let detail = text
    try {
      const j = JSON.parse(text) as { detail?: string | unknown }
      if (typeof j.detail === 'string') detail = j.detail
      else if (j.detail) detail = JSON.stringify(j.detail)
    } catch {
      /* use text */
    }
    throw new Error(detail || res.statusText)
  }
  if (!text) return undefined as T
  try {
    return JSON.parse(text) as T
  } catch {
    return text as unknown as T
  }
}

export function cameraStreamUrl(): string {
  const token = getToken()
  if (!token) return ''
  return `${apiUrl('/api/camera/stream')}?access_token=${encodeURIComponent(token)}`
}

/** Relative path under server recordings root; token as query for `<video src>`. */
export function recordingsMediaUrl(relpath: string): string {
  const token = getToken()
  const q = new URLSearchParams({ path: relpath })
  if (token) q.set('access_token', token)
  return `${apiUrl('/api/recordings/media')}?${q.toString()}`
}
