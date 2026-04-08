import { useEffect, useState } from 'react'
import { apiUrl, getToken } from '../api/client'

type Props = {
  /** Must be true only after `/api/camera/preview/start` succeeds */
  active: boolean
  className?: string
  alt?: string
}

/**
 * Live camera preview for the FastAPI + qt_bridge stack.
 * Uses JPEG snapshot polling because multipart MJPEG in <img src> is unreliable in Chrome
 * and cannot send Authorization headers (token is passed as query param like the stream URL).
 */
export function CameraLivePreview({ active, className = '', alt = 'Live camera preview' }: Props) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [status, setStatus] = useState<string>('')

  useEffect(() => {
    if (!active) {
      setBlobUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev)
        return null
      })
      setStatus('')
      return
    }

    const token = getToken()
    if (!token) {
      setStatus('Not signed in')
      return
    }

    let cancelled = false
    let intervalId = 0

    const poll = async () => {
      if (cancelled) return
      try {
        const u = `${apiUrl('/api/camera/snapshot')}?access_token=${encodeURIComponent(token)}&_=${Date.now()}`
        const res = await fetch(u, { cache: 'no-store', credentials: 'omit' })
        if (cancelled) return
        if (res.ok) {
          const blob = await res.blob()
          if (cancelled) return
          const next = URL.createObjectURL(blob)
          setBlobUrl((prev) => {
            if (prev) URL.revokeObjectURL(prev)
            return next
          })
          setStatus('')
        } else if (res.status === 404) {
          setStatus('Starting camera… (close the desktop ZIMON app if the camera is in use)')
        } else if (res.status === 401) {
          setStatus('Session expired — sign in again')
        } else {
          setStatus(`Preview error (${res.status})`)
        }
      } catch {
        if (!cancelled) setStatus('Network error — is the API running?')
      }
    }

    void poll()
    intervalId = window.setInterval(poll, 80)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
      setBlobUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev)
        return null
      })
    }
  }, [active])

  if (!active) return null

  if (blobUrl) {
    return <img src={blobUrl} alt={alt} className={className} />
  }

  return (
    <div
      className={`flex min-h-[200px] items-center justify-center text-sm text-zimon-muted ${className}`}
    >
      {status || 'Connecting to camera…'}
    </div>
  )
}
