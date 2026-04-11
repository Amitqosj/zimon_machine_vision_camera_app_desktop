import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { AlertCircle, AlertTriangle, CheckCircle2, Info, X } from 'lucide-react'

export type ToastVariant = 'success' | 'error' | 'warning' | 'info'

export type ToastItem = {
  id: string
  message: string
  variant: ToastVariant
}

const DEFAULT_DURATION_MS = 3000

type ToastApi = {
  show: (message: string, variant: ToastVariant, durationMs?: number) => void
  success: (message: string, durationMs?: number) => void
  error: (message: string, durationMs?: number) => void
  warning: (message: string, durationMs?: number) => void
  info: (message: string, durationMs?: number) => void
  dismiss: (id: string) => void
}

const ToastContext = createContext<ToastApi | null>(null)

const variantStyles: Record<
  ToastVariant,
  { box: string; icon: typeof CheckCircle2; IconClass: string }
> = {
  success: {
    box: 'border-emerald-400/80 bg-emerald-50 text-emerald-950 shadow-emerald-900/10 dark:border-emerald-500/40 dark:bg-emerald-950/90 dark:text-emerald-50',
    icon: CheckCircle2,
    IconClass: 'text-emerald-600 dark:text-emerald-400',
  },
  error: {
    box: 'border-red-400/80 bg-red-50 text-red-950 shadow-red-900/10 dark:border-red-500/40 dark:bg-red-950/90 dark:text-red-50',
    icon: AlertCircle,
    IconClass: 'text-red-600 dark:text-red-400',
  },
  warning: {
    box: 'border-amber-400/80 bg-amber-50 text-amber-950 shadow-amber-900/10 dark:border-amber-500/40 dark:bg-amber-950/90 dark:text-amber-50',
    icon: AlertTriangle,
    IconClass: 'text-amber-600 dark:text-amber-400',
  },
  info: {
    box: 'border-blue-400/80 bg-blue-50 text-blue-950 shadow-blue-900/10 dark:border-blue-500/40 dark:bg-blue-950/90 dark:text-blue-50',
    icon: Info,
    IconClass: 'text-blue-600 dark:text-blue-400',
  },
}

function ToastViewport({ toasts, onDismiss }: { toasts: ToastItem[]; onDismiss: (id: string) => void }) {
  return (
    <div
      className="pointer-events-none fixed right-4 top-4 z-[9999] flex max-w-[min(100vw-2rem,24rem)] flex-col gap-2 sm:right-6 sm:top-5"
      aria-live="polite"
      aria-relevant="additions text"
    >
      {toasts.map((t) => {
        const cfg = variantStyles[t.variant]
        const Icon = cfg.icon
        return (
          <div
            key={t.id}
            role="status"
            className={`pointer-events-auto flex animate-toast-in items-start gap-3 rounded-xl border px-4 py-3 text-sm font-medium shadow-lg backdrop-blur-sm ${cfg.box}`}
          >
            <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${cfg.IconClass}`} strokeWidth={2} aria-hidden />
            <p className="min-w-0 flex-1 leading-snug">{t.message}</p>
            <button
              type="button"
              onClick={() => onDismiss(t.id)}
              className="-m-1 shrink-0 rounded-lg p-1 opacity-70 transition hover:opacity-100"
              aria-label="Dismiss notification"
            >
              <X className="h-4 w-4" strokeWidth={2} />
            </button>
          </div>
        )
      })}
    </div>
  )
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([])
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  const dismiss = useCallback((id: string) => {
    const t = timers.current.get(id)
    if (t) {
      clearTimeout(t)
      timers.current.delete(id)
    }
    setToasts((prev) => prev.filter((x) => x.id !== id))
  }, [])

  const show = useCallback(
    (message: string, variant: ToastVariant, durationMs: number = DEFAULT_DURATION_MS) => {
      const id =
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`
      const trimmed = message.trim() || 'Notification'
      setToasts((prev) => [...prev, { id, message: trimmed, variant }])
      const timer = setTimeout(() => {
        timers.current.delete(id)
        setToasts((prev) => prev.filter((x) => x.id !== id))
      }, durationMs)
      timers.current.set(id, timer)
    },
    [],
  )

  const success = useCallback((m: string, d?: number) => show(m, 'success', d), [show])
  const error = useCallback((m: string, d?: number) => show(m, 'error', d), [show])
  const warning = useCallback((m: string, d?: number) => show(m, 'warning', d), [show])
  const info = useCallback((m: string, d?: number) => show(m, 'info', d), [show])

  const value = useMemo(
    () => ({ show, success, error, warning, info, dismiss }),
    [show, success, error, warning, info, dismiss],
  )

  useEffect(
    () => () => {
      timers.current.forEach((t) => clearTimeout(t))
      timers.current.clear()
    },
    [],
  )

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error('useToast must be used within ToastProvider')
  return ctx
}
