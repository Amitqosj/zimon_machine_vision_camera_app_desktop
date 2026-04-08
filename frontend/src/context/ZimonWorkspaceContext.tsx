import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import type { ZimonProtocol } from '../types/zimonProtocol'

type Ctx = {
  activeProtocol: ZimonProtocol | null
  setActiveProtocol: (p: ZimonProtocol | null) => void
  experimentRunId: string | null
  setExperimentRunId: (id: string | null) => void
  currentPhaseLabel: string
  setCurrentPhaseLabel: (s: string) => void
  actionLog: string[]
  appendActionLog: (line: string) => void
  clearActionLog: () => void
}

const ZimonWorkspaceContext = createContext<Ctx | null>(null)

function ts() {
  return new Date().toISOString().slice(11, 19)
}

export function ZimonWorkspaceProvider({ children }: { children: ReactNode }) {
  const [activeProtocol, setActiveProtocol] = useState<ZimonProtocol | null>(null)
  const [experimentRunId, setExperimentRunId] = useState<string | null>(null)
  const [currentPhaseLabel, setCurrentPhaseLabel] = useState('Idle')
  const [actionLog, setActionLog] = useState<string[]>([])

  const appendActionLog = useCallback((line: string) => {
    setActionLog((prev) => [`[${ts()}] ${line}`, ...prev].slice(0, 200))
  }, [])

  const clearActionLog = useCallback(() => setActionLog([]), [])

  const value = useMemo(
    () => ({
      activeProtocol,
      setActiveProtocol,
      experimentRunId,
      setExperimentRunId,
      currentPhaseLabel,
      setCurrentPhaseLabel,
      actionLog,
      appendActionLog,
      clearActionLog,
    }),
    [
      activeProtocol,
      experimentRunId,
      currentPhaseLabel,
      actionLog,
      appendActionLog,
      clearActionLog,
    ],
  )

  return <ZimonWorkspaceContext.Provider value={value}>{children}</ZimonWorkspaceContext.Provider>
}

export function useZimonWorkspace() {
  const c = useContext(ZimonWorkspaceContext)
  if (!c) throw new Error('useZimonWorkspace must be used within ZimonWorkspaceProvider')
  return c
}
