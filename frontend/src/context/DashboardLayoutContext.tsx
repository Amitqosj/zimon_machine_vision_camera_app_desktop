import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { ASSAYS, RECIPES, type RecipeDef } from '../features/dashboard/constants'

const PLATE_KEY = 'zimon-well-plate'

/** Center content tabs above the live camera (dashboard). */
export type WorkspaceTab = 'adult' | 'recipes' | 'experiments'

/** Top pill toggle above sub-tabs (Adult vs Recipes). */
export type WorkspaceBand = 'adult' | 'recipes'

type Ctx = {
  workspaceBand: WorkspaceBand
  setWorkspaceBand: (b: WorkspaceBand) => void
  workspaceTab: WorkspaceTab
  setWorkspaceTab: (t: WorkspaceTab) => void
  selectedAssayId: string
  setSelectedAssayId: (id: string) => void
  selectedPlateWells: 12 | 24 | 48 | 96
  setSelectedPlateWells: (w: 12 | 24 | 48 | 96) => void
  selectedRecipeId: string
  setSelectedRecipeId: (id: string) => void
  applyRecipe: (r: RecipeDef) => void
  showAllAssays: boolean
  setShowAllAssays: (v: boolean) => void
  /** Current line in the bottom hint bar (above system footer). */
  footerHintLine: string
  cycleFooterHint: (delta: number) => void
}

const DashboardLayoutContext = createContext<Ctx | null>(null)

function loadPlate(): 12 | 24 | 48 | 96 {
  try {
    const n = Number(localStorage.getItem(PLATE_KEY))
    if (n === 12 || n === 24 || n === 48 || n === 96) return n
  } catch {
    /* ignore */
  }
  return 96
}

export function DashboardLayoutProvider({ children }: { children: React.ReactNode }) {
  const [workspaceBand, setWorkspaceBandState] = useState<WorkspaceBand>('recipes')
  const [workspaceTab, setWorkspaceTabState] = useState<WorkspaceTab>('recipes')

  const setWorkspaceBand = useCallback((b: WorkspaceBand) => {
    setWorkspaceBandState(b)
    setWorkspaceTabState(b)
  }, [])

  const setWorkspaceTab = useCallback((t: WorkspaceTab) => {
    setWorkspaceTabState(t)
    if (t === 'adult' || t === 'recipes') {
      setWorkspaceBandState(t)
    }
  }, [])
  const [selectedAssayId, setSelectedAssayId] = useState(ASSAYS[0]?.id ?? 'multi-well')
  const [selectedPlateWells, setPlateState] = useState<12 | 24 | 48 | 96>(loadPlate)
  const [selectedRecipeId, setSelectedRecipeId] = useState(RECIPES[0]?.id ?? 'custom')
  const [showAllAssays, setShowAllAssays] = useState(false)

  const setSelectedPlateWells = useCallback((w: 12 | 24 | 48 | 96) => {
    setPlateState(w)
    try {
      localStorage.setItem(PLATE_KEY, String(w))
    } catch {
      /* ignore */
    }
  }, [])

  const applyRecipe = useCallback((r: RecipeDef) => {
    setSelectedRecipeId(r.id)
    window.dispatchEvent(
      new CustomEvent('zimon-apply-recipe', {
        detail: { durationS: r.durationS, fps: r.fps },
      }),
    )
  }, [])

  const footerHintSlides = useMemo(() => {
    const recipe = RECIPES.find((x) => x.id === selectedRecipeId)
    const assay = ASSAYS.find((a) => a.id === selectedAssayId)
    const slides: string[] = []
    if (recipe?.tip) {
      const body = recipe.tip.replace(/^For\s+[^,]+,\s*/i, '').trim()
      slides.push(`For "${recipe.title}": ${body}`)
    }
    if (assay) {
      slides.push(`${assay.title}: ${assay.description}`)
    }
    return slides.length > 0
      ? slides
      : ['Select an assay and recipe for contextual guidance.']
  }, [selectedRecipeId, selectedAssayId])

  const [footerHintIndex, setFooterHintIndex] = useState(0)

  useEffect(() => {
    setFooterHintIndex(0)
  }, [selectedRecipeId, selectedAssayId])

  const footerHintLine = useMemo(() => {
    const n = footerHintSlides.length
    return footerHintSlides[((footerHintIndex % n) + n) % n] ?? ''
  }, [footerHintSlides, footerHintIndex])

  const cycleFooterHint = useCallback(
    (delta: number) => {
      setFooterHintIndex((s) => {
        const n = Math.max(1, footerHintSlides.length)
        return (s + delta + n * 32) % n
      })
    },
    [footerHintSlides.length],
  )

  const value = useMemo(
    () => ({
      workspaceBand,
      setWorkspaceBand,
      workspaceTab,
      setWorkspaceTab,
      selectedAssayId,
      setSelectedAssayId,
      selectedPlateWells,
      setSelectedPlateWells,
      selectedRecipeId,
      setSelectedRecipeId,
      applyRecipe,
      showAllAssays,
      setShowAllAssays,
      footerHintLine,
      cycleFooterHint,
    }),
    [
      workspaceBand,
      workspaceTab,
      setWorkspaceTab,
      setWorkspaceBand,
      selectedAssayId,
      selectedPlateWells,
      selectedRecipeId,
      showAllAssays,
      footerHintLine,
      cycleFooterHint,
      setSelectedPlateWells,
      applyRecipe,
    ],
  )

  return (
    <DashboardLayoutContext.Provider value={value}>{children}</DashboardLayoutContext.Provider>
  )
}

export function useDashboardLayout() {
  const c = useContext(DashboardLayoutContext)
  if (!c) throw new Error('useDashboardLayout must be used within DashboardLayoutProvider')
  return c
}
