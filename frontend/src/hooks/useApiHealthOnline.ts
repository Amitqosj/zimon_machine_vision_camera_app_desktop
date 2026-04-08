import { useEffect, useState } from 'react'
import { apiUrl } from '../api/client'

/** True when GET /api/health succeeds (API + typical camera stack reachable). */
export function useApiHealthOnline() {
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      try {
        const r = await fetch(apiUrl('/api/health'))
        if (!cancelled) setOnline(r.ok)
      } catch {
        if (!cancelled) setOnline(false)
      }
    }
    void run()
    const id = window.setInterval(run, 15000)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [])

  return online
}
