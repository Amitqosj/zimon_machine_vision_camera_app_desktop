/**
 * FastAPI route map (prefix `/api`). Base URL: `VITE_API_URL` or http://127.0.0.1:8000
 *
 * Auth: `Authorization: Bearer <token>` on all routes except `/api/auth/*`, `/api/health`,
 * and camera stream/snapshot (Bearer or `?access_token=`).
 *
 * Run API: `uvicorn backend.api.main:app --host 127.0.0.1 --port 8000` from repo root (venv).
 * PyQt (`python main.py`) uses in-process Arduino/camera; web UI needs the API process — do not
 * share the same COM port between PyQt and the API at once.
 */
export const ZIMON_API = {
  health: '/api/health',
  auth: {
    login: '/api/auth/login',
    forgotPassword: '/api/auth/forgot-password',
    me: '/api/auth/me',
    logout: '/api/auth/logout',
  },
  users: {
    list: '/api/users',
    one: (id: number) => `/api/users/${id}`,
    resetPassword: (id: number) => `/api/users/${id}/reset-password`,
    lock: (id: number) => `/api/users/${id}/lock`,
    unlock: (id: number) => `/api/users/${id}/unlock`,
  },
  internal: {
    recoveryAccess: '/api/internal/recovery-access',
  },
  arduino: {
    ports: '/api/arduino/ports',
    status: '/api/arduino/status',
    connect: '/api/arduino/connect',
    autoConnect: '/api/arduino/auto-connect',
    disconnect: '/api/arduino/disconnect',
    command: '/api/arduino/command',
    temperature: '/api/arduino/temperature',
  },
  camera: {
    list: '/api/camera/list',
    refresh: '/api/camera/refresh',
    previewStart: (cameraName: string) =>
      `/api/camera/preview/start?camera_name=${encodeURIComponent(cameraName)}`,
    previewStop: (cameraName: string) =>
      `/api/camera/preview/stop?camera_name=${encodeURIComponent(cameraName)}`,
    previewStatus: '/api/camera/preview/status',
    settings: (cameraName: string) =>
      `/api/camera/settings?camera_name=${encodeURIComponent(cameraName)}`,
    supportedResolutions: (cameraName: string) =>
      `/api/camera/supported-resolutions?camera_name=${encodeURIComponent(cameraName)}`,
    meta: (cameraName: string) =>
      `/api/camera/meta?camera_name=${encodeURIComponent(cameraName)}`,
    stream: '/api/camera/stream',
    snapshot: '/api/camera/snapshot',
  },
  experiment: {
    start: '/api/experiment/start',
    stop: '/api/experiment/stop',
    status: '/api/experiment/status',
  },
  recordings: {
    list: '/api/recordings/list',
    media: '/api/recordings/media',
  },
  presets: {
    list: '/api/presets',
    one: (id: number) => `/api/presets/${id}`,
  },
  analysis: {
    available: '/api/analysis/available',
    jobs: '/api/analysis/jobs',
    job: (jobId: string) => `/api/analysis/jobs/${jobId}`,
  },
  settings: {
    get: '/api/settings',
    put: '/api/settings',
    zebrazoomBrowse: '/api/settings/zebrazoom/browse',
    zebrazoomTest: '/api/settings/zebrazoom/test',
    zebrazoomStatus: '/api/settings/zebrazoom/status',
  },
} as const
