import type { LucideIcon } from 'lucide-react'
import {
  Activity,
  Bell,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  FolderOpen,
  Footprints,
  LayoutGrid,
  Settings,
  SlidersHorizontal,
  Zap,
} from 'lucide-react'
import { Fragment, useEffect, useMemo, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { ThemeToggle } from '../components/ThemeToggle'
import { useAuth } from '../context/AuthContext'
import { useDashboardLayout } from '../context/DashboardLayoutContext'
import { useHardwareStatus } from '../context/HardwareStatusContext'
import { ZIMON_LOGO_URL } from '../constants/branding'
import { ASSAYS, PLATES, RECIPES } from '../features/dashboard/constants'

const RECIPE_ICONS: Record<string, LucideIcon> = {
  custom: SlidersHorizontal,
  'larval-loco': Footprints,
  anxiety: Activity,
  predator: Zap,
}

export function AppLayout() {
  const { user } = useAuth()
  const ctx = useDashboardLayout()
  const hw = useHardwareStatus()
  const location = useLocation()
  const showExecutionPanels = useMemo(
    () => /^\/app\/(adult|larval)\/?$/.test(location.pathname),
    [location.pathname],
  )
  const [now, setNow] = useState(() => new Date())

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 1000)
    return () => window.clearInterval(id)
  }, [])

  const arduinoOk = hw.arduinoOk
  const cameraPreview = hw.previewing.length > 0
  const expRunning = hw.expRunning
  const temp = hw.temperatureC

  const assaysShown = ctx.showAllAssays ? ASSAYS : ASSAYS.slice(0, 5)

  return (
    <div className="flex min-h-screen flex-col bg-zimon-bg text-zimon-fg dark:bg-transparent">
      <header className="shrink-0 bg-zimon-panel/95 px-4 py-3 backdrop-blur-xl dark:bg-slate-950/80 md:px-6">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-3">
          <div className="flex min-w-0 shrink-0 items-center gap-3 md:max-w-[min(100%,280px)]">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center overflow-hidden rounded-full bg-slate-200/90 dark:bg-slate-900/45">
              <img
                src={ZIMON_LOGO_URL}
                alt="ZIMON"
                width={48}
                height={48}
                className="h-full w-full object-cover"
                decoding="async"
              />
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <div className="text-lg font-bold tracking-tight text-zimon-fg">ZIMON</div>
                <span
                  className={[
                    'hidden rounded-full border px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide sm:inline',
                    hw.environmentOk && cameraPreview
                      ? 'border-emerald-500/35 text-emerald-600 dark:text-emerald-400'
                      : 'border-amber-500/30 text-amber-700 dark:text-amber-300',
                  ].join(' ')}
                  title={hw.environmentMessage}
                >
                  {hw.environmentOk && cameraPreview ? 'System ready' : 'Check environment'}
                </span>
              </div>
              <div className="truncate text-[11px] text-zimon-muted">
                Zebrafish Integrated Motion &amp; Optical Neuroanalysis Chamber
              </div>
            </div>
          </div>

          <nav
            className="flex min-w-0 flex-1 flex-wrap items-center justify-center gap-1 sm:gap-1.5"
            aria-label="Main modules"
          >
            {(
              [
                { to: '/app/adult', label: 'Adult' },
                { to: '/app/larval', label: 'Larval' },
                { to: '/app/environment', label: 'Environment' },
                { to: '/app/protocol-builder', label: 'Protocol Builder' },
                { to: '/app/experiments', label: 'Experiments' },
              ] as const
            ).map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  [
                    'rounded-full px-2.5 py-1.5 text-[11px] font-semibold transition-all sm:px-3 sm:text-xs',
                    isActive
                      ? 'bg-gradient-to-r from-blue-600 to-sky-500 text-white shadow-md shadow-blue-600/25'
                      : 'text-slate-600 hover:bg-white/60 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-200',
                  ].join(' ')
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
            <button
              type="button"
              className="relative rounded-xl border-0 bg-slate-200/80 p-2.5 text-slate-600 transition-colors hover:bg-blue-500/15 hover:text-blue-700 dark:bg-slate-900/70 dark:text-slate-400 dark:hover:bg-cyan-500/10 dark:hover:text-cyan-200"
              title="Notifications"
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5" />
              <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white dark:ring-slate-950" />
            </button>
            <ThemeToggle variant="toolbar" />
            <Link
              to="/app/settings"
              className="rounded-xl border-0 bg-slate-200/80 p-2.5 text-slate-600 transition-colors hover:bg-blue-500/15 hover:text-blue-700 dark:bg-slate-900/70 dark:text-slate-400 dark:hover:bg-cyan-500/10 dark:hover:text-cyan-200"
              title="Settings"
            >
              <Settings className="h-5 w-5" />
            </Link>
            <Link
              to="/app/account"
              className="flex items-center gap-2 rounded-xl border-0 bg-slate-200/80 px-3 py-2 text-sm font-medium text-zimon-fg transition-colors hover:bg-blue-500/10 dark:bg-slate-900/70 dark:hover:bg-cyan-500/10"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600/15 text-xs font-bold text-blue-700 dark:bg-cyan-500/20 dark:text-cyan-300">
                {(user?.full_name || user?.username || 'R').slice(0, 1).toUpperCase()}
              </span>
              <span className="hidden max-w-[100px] truncate sm:inline">
                {user?.full_name || user?.username || 'Researcher'}
              </span>
              <ChevronDown className="h-4 w-4 text-zimon-muted" />
            </Link>
          </div>
        </div>
      </header>

      <div className="flex min-h-0 flex-1 gap-3 px-3 py-3 md:px-4">
        {showExecutionPanels ? (
        <aside className="zimon-glass-panel hidden w-[260px] shrink-0 flex-col p-3 lg:flex">
          <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.15em] text-zimon-muted">
            Top recording assays
          </div>
          <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto">
            {assaysShown.map((a) => {
              const sel = ctx.selectedAssayId === a.id
              return (
                <button
                  key={a.id}
                  type="button"
                  onClick={() => ctx.setSelectedAssayId(a.id)}
                  className={[
                    'rounded-xl border p-3 text-left transition-all duration-200 hover:-translate-y-0.5',
                    sel
                      ? 'border-cyan-400/50 bg-cyan-500/10 shadow-[0_0_24px_var(--zimon-glow)] ring-1 ring-cyan-400/30 dark:border-cyan-400/40'
                      : 'border-zimon-border/60 bg-zimon-card/30 hover:border-cyan-400/25 hover:shadow-md dark:bg-slate-900/30',
                  ].join(' ')}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-xl leading-none">{a.icon}</span>
                    <div>
                      <div className="text-sm font-semibold text-zimon-fg">{a.title}</div>
                      <div className="mt-1 text-[11px] leading-snug text-zimon-muted">{a.description}</div>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
          <button
            type="button"
            onClick={() => ctx.setShowAllAssays(!ctx.showAllAssays)}
            className="mt-3 flex items-center justify-center gap-2 rounded-xl border border-zimon-border py-2.5 text-xs font-semibold text-zimon-fg transition-colors hover:border-cyan-400/30 hover:bg-zimon-card/60 dark:hover:bg-slate-800/50"
          >
            <LayoutGrid className="h-4 w-4" />
            {ctx.showAllAssays ? 'Show fewer' : 'View all assays'}
          </button>
        </aside>
        ) : null}

        <main className="zimon-glass-panel min-h-0 min-w-0 flex-1 overflow-auto p-4 md:p-5 dark:border-cyan-500/10 dark:bg-slate-950/35">
          <Outlet />
        </main>

        {showExecutionPanels ? (
        <aside className="zimon-glass-panel hidden w-[248px] shrink-0 flex-col gap-4 p-3 xl:flex">
          <div>
            <div className="mb-2.5 text-[10px] font-bold uppercase tracking-[0.15em] text-zimon-muted dark:text-cyan-200/55">
              Select well plate
            </div>
            <div className="grid grid-cols-2 gap-3">
              {PLATES.map((p) => {
                const sel = ctx.selectedPlateWells === p.wells
                const typeLine = p.label.replace(/^\d+\s+/, '').trim()
                return (
                  <button
                    key={p.wells}
                    type="button"
                    onClick={() => ctx.setSelectedPlateWells(p.wells)}
                    className={[
                      'flex aspect-square w-full flex-col items-center justify-center gap-1 rounded-xl border p-2 text-center transition-all duration-200',
                      sel
                        ? 'border-cyan-400/55 bg-cyan-500/10 shadow-[0_0_22px_var(--zimon-glow)] ring-1 ring-cyan-400/35 dark:border-cyan-400/50'
                        : 'border-zimon-border/60 bg-zimon-card/40 hover:-translate-y-0.5 hover:border-cyan-400/30 hover:shadow-md dark:bg-slate-950/45 dark:hover:border-cyan-400/25',
                    ].join(' ')}
                  >
                    <span className="text-xl font-bold tabular-nums leading-none text-zimon-fg dark:text-cyan-50/95">
                      {p.wells}
                    </span>
                    <span className="max-w-[5.5rem] text-[8px] font-semibold leading-tight text-zimon-muted dark:text-slate-400">
                      {typeLine}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>
          <div className="flex min-h-0 flex-1 flex-col">
            <div className="mb-2.5 text-[10px] font-bold uppercase tracking-[0.15em] text-zimon-muted dark:text-cyan-200/55">
              Recipes
            </div>
            <div className="flex flex-col gap-2 overflow-y-auto pr-0.5">
              {RECIPES.map((r) => {
                const sel = ctx.selectedRecipeId === r.id
                const Icon = RECIPE_ICONS[r.id] ?? SlidersHorizontal
                return (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => ctx.applyRecipe(r)}
                    className={[
                      'flex w-full items-start gap-2.5 rounded-xl border p-2.5 text-left shadow-sm transition-all duration-200',
                      sel
                        ? 'border-cyan-400/45 bg-cyan-500/10 shadow-[0_0_18px_-4px_var(--zimon-glow)] ring-1 ring-cyan-400/25 dark:border-cyan-400/40'
                        : 'border-zimon-border/60 bg-zimon-card/50 hover:border-cyan-400/25 hover:bg-zimon-card/80 dark:bg-slate-950/50 dark:hover:border-cyan-400/20',
                    ].join(' ')}
                  >
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-zimon-border/50 bg-zimon-panel/90 text-cyan-600 dark:border-cyan-500/15 dark:bg-slate-900/70 dark:text-cyan-400">
                      <Icon className="h-4 w-4" strokeWidth={2} />
                    </span>
                    <div className="min-w-0 flex-1 pt-0.5">
                      <div className="text-xs font-bold leading-tight text-zimon-fg dark:text-cyan-50/90">{r.title}</div>
                      <div className="mt-1 text-[10px] leading-snug text-zimon-muted">{r.blurb}</div>
                    </div>
                  </button>
                )
              })}
            </div>
            <Link
              to="/app/protocol-builder"
              className="mt-2.5 flex items-center justify-center gap-2 rounded-xl border border-zimon-border py-2 text-xs font-semibold text-zimon-fg transition-colors hover:border-cyan-400/30 hover:bg-zimon-card/60 dark:border-cyan-500/15 dark:hover:bg-slate-800/50"
            >
              <FolderOpen className="h-4 w-4" />
              Protocol Builder
            </Link>
          </div>
        </aside>
        ) : null}
      </div>

      <div className="shrink-0 border-t border-cyan-500/15 bg-slate-950/88 px-3 py-1.5 shadow-[inset_0_1px_0_rgba(56,189,248,0.06)] backdrop-blur-md dark:border-cyan-500/20 dark:bg-slate-950/92">
        <div className="mx-auto flex max-w-[1400px] items-center gap-2 sm:gap-3">
          <div className="min-w-0 flex-1 text-left text-[10px] leading-tight text-slate-400 sm:text-[11px] dark:text-slate-400">
            <p>{ctx.footerHintLine}</p>
            <p
              className={
                hw.environmentOk
                  ? 'mt-0.5 text-emerald-500/90 dark:text-emerald-400/90'
                  : 'mt-0.5 text-amber-600 dark:text-amber-300/90'
              }
            >
              {hw.environmentMessage}
            </p>
          </div>
          <div className="flex shrink-0 items-center gap-0.5 border-l border-cyan-500/10 pl-2 dark:border-cyan-500/15">
            <button
              type="button"
              className="rounded-md p-1 text-slate-500 transition-colors hover:bg-slate-800/90 hover:text-cyan-200 dark:text-slate-400 dark:hover:text-cyan-100"
              aria-label="Previous hint"
              onClick={() => ctx.cycleFooterHint(-1)}
            >
              <ChevronLeft className="h-3.5 w-3.5" strokeWidth={2.25} />
            </button>
            <button
              type="button"
              className="rounded-md p-1 text-slate-500 transition-colors hover:bg-slate-800/90 hover:text-cyan-200 dark:text-slate-400 dark:hover:text-cyan-100"
              aria-label="Next hint"
              onClick={() => ctx.cycleFooterHint(1)}
            >
              <ChevronRight className="h-3.5 w-3.5" strokeWidth={2.25} />
            </button>
          </div>
        </div>
      </div>

      <footer className="shrink-0 border-t border-zimon-border/70 bg-zimon-panel/95 px-4 py-3 text-[11px] text-zimon-muted backdrop-blur-xl dark:border-cyan-500/10 dark:bg-slate-950/80">
        <div className="mx-auto flex max-w-[1400px] flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between">
          <div className="flex min-w-0 flex-1 flex-wrap items-center justify-center gap-x-2 gap-y-2 sm:justify-start sm:gap-x-0 sm:gap-y-2">
            {(
              [
                <span key="sys" className="shrink-0 whitespace-nowrap px-1 sm:px-2">
                  System:{' '}
                  <span
                    className={
                      arduinoOk ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600 dark:text-amber-400'
                    }
                  >
                    {arduinoOk ? 'Connected' : 'Disconnected'}
                  </span>
                </span>,
                <span key="cam" className="shrink-0 whitespace-nowrap px-1 sm:px-2">
                  Camera:{' '}
                  <span className={cameraPreview ? 'text-emerald-600 dark:text-emerald-400' : 'text-zimon-fg'}>
                    {cameraPreview ? 'Streaming' : 'Idle'}
                  </span>
                </span>,
                <span key="chm" className="shrink-0 whitespace-nowrap px-1 sm:px-2">
                  Chamber:{' '}
                  <span className={expRunning ? 'text-sky-600 dark:text-sky-400' : 'text-zimon-fg'}>
                    {expRunning ? 'Recording' : 'Idle'}
                  </span>
                </span>,
                <span key="tmp" className="shrink-0 whitespace-nowrap px-1 sm:px-2">
                  Temperature:{' '}
                  <span className="tabular-nums text-zimon-fg">{temp != null ? `${temp.toFixed(1)} °C` : '—'}</span>
                </span>,
                <span key="h2o" className="shrink-0 whitespace-nowrap px-1 sm:px-2">
                  Water flow:{' '}
                  <span className="text-zimon-fg">{arduinoOk ? 'Adjust in dashboard' : '—'}</span>
                </span>,
              ] as const
            ).map((node, i) => (
              <Fragment key={`status-${i}`}>
                {i > 0 ? (
                  <span
                    className="shrink-0 select-none px-2 text-sm font-light text-zimon-border/70 sm:px-5 dark:text-cyan-500/35"
                    aria-hidden
                  >
                    |
                  </span>
                ) : null}
                {node}
              </Fragment>
            ))}
          </div>
          <div className="shrink-0 text-center tabular-nums text-zimon-fg sm:text-right">
            {now.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' })}{' '}
            {now.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
          </div>
        </div>
      </footer>
    </div>
  )
}
