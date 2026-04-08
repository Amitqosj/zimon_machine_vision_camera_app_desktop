import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../../../api/client'

type CamList = { cameras: string[] }
type CamMeta = {
  type: string
  fps: number | null
  resolution: [number, number] | null
  zoom: number | null
}
type ResList = { resolutions: { width: number; height: number }[] }
type PreviewStatus = { previewing: string[] }

const RES_PRESETS = [
  '640x480',
  '800x600',
  '1024x768',
  '1280x720',
  '1280x1024',
  '1920x1080',
  '2048x1536',
]

export function useDashboardCamera() {
  const [cameras, setCameras] = useState<string[]>([])
  const [cam, setCam] = useState('')
  const [previewOn, setPreviewOn] = useState(false)
  const [meta, setMeta] = useState<CamMeta | null>(null)
  const [supportedRes, setSupportedRes] = useState<{ width: number; height: number }[]>([])
  const [fps, setFps] = useState(30)
  const [zoomPct, setZoomPct] = useState(100)
  const [resolutionPick, setResolutionPick] = useState('1920x1080')
  const [err, setErr] = useState('')

  const refreshCameras = useCallback(async () => {
    try {
      await apiFetch('/api/camera/refresh', { method: 'POST' })
      const r = await apiFetch<CamList>('/api/camera/list')
      setCameras(r.cameras)
      setCam((prev) =>
        prev && r.cameras.includes(prev) ? prev : r.cameras[0] || '',
      )
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }, [])

  useEffect(() => {
    void refreshCameras()
  }, [refreshCameras])

  useEffect(() => {
    let cancelled = false
    const syncPreview = async () => {
      try {
        const r = await apiFetch<PreviewStatus>('/api/camera/preview/status')
        if (cancelled) return
        if (!cam) {
          setPreviewOn(false)
          return
        }
        setPreviewOn(r.previewing.includes(cam))
      } catch {
        /* keep */
      }
    }
    void syncPreview()
    const id = window.setInterval(() => void syncPreview(), 2500)
    return () => {
      cancelled = true
      window.clearInterval(id)
    }
  }, [cam])

  useEffect(() => {
    if (!cam) return
    const load = async () => {
      try {
        const m = await apiFetch<CamMeta>(
          `/api/camera/meta?camera_name=${encodeURIComponent(cam)}`,
        )
        setMeta(m)
        if (m.zoom != null) setZoomPct(Math.round(m.zoom * 100))
        if (m.resolution) {
          const [w, h] = m.resolution
          setResolutionPick(`${w}x${h}`)
        }
        if (m.fps != null) setFps(Math.round(Number(m.fps)))
      } catch {
        setMeta(null)
      }
      try {
        const sr = await apiFetch<ResList>(
          `/api/camera/supported-resolutions?camera_name=${encodeURIComponent(cam)}`,
        )
        setSupportedRes(sr.resolutions || [])
      } catch {
        setSupportedRes([])
      }
    }
    void load()
  }, [cam, previewOn])

  async function startPreview() {
    if (!cam) return
    setErr('')
    try {
      await apiFetch(
        `/api/camera/preview/start?camera_name=${encodeURIComponent(cam)}`,
        { method: 'POST' },
      )
      setPreviewOn(true)
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function stopPreview() {
    if (!cam) return
    try {
      await apiFetch(
        `/api/camera/preview/stop?camera_name=${encodeURIComponent(cam)}`,
        { method: 'POST' },
      )
    } finally {
      setPreviewOn(false)
    }
  }

  async function applyFps() {
    if (!cam) return
    setErr('')
    try {
      await apiFetch(
        `/api/camera/settings?camera_name=${encodeURIComponent(cam)}`,
        {
          method: 'POST',
          body: JSON.stringify({ setting: 'fps', value: fps }),
        },
      )
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function applyZoom() {
    if (!cam) return
    setErr('')
    try {
      await apiFetch(
        `/api/camera/settings?camera_name=${encodeURIComponent(cam)}`,
        {
          method: 'POST',
          body: JSON.stringify({ setting: 'zoom', value: zoomPct / 100 }),
        },
      )
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  async function applyResolution() {
    if (!cam) return
    const [w, h] = resolutionPick.split('x').map(Number)
    if (!w || !h) return
    setErr('')
    try {
      await apiFetch(
        `/api/camera/settings?camera_name=${encodeURIComponent(cam)}`,
        {
          method: 'POST',
          body: JSON.stringify({ setting: 'resolution', value: [w, h] }),
        },
      )
      if (previewOn) {
        await apiFetch(
          `/api/camera/preview/stop?camera_name=${encodeURIComponent(cam)}`,
          { method: 'POST' },
        )
        await apiFetch(
          `/api/camera/preview/start?camera_name=${encodeURIComponent(cam)}`,
          { method: 'POST' },
        )
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e))
    }
  }

  function bumpFps(delta: number) {
    setFps((f) => Math.min(120, Math.max(1, f + delta)))
  }

  return {
    cameras,
    cam,
    setCam,
    previewOn,
    meta,
    supportedRes,
    fps,
    setFps,
    bumpFps,
    zoomPct,
    setZoomPct,
    resolutionPick,
    setResolutionPick,
    err,
    setErr,
    refreshCameras,
    startPreview,
    stopPreview,
    applyFps,
    applyZoom,
    applyResolution,
    resPresets: RES_PRESETS,
  }
}
