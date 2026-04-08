import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

type Props = {
  className?: string
  /** Flat toolbar chip: no outline (e.g. app header). */
  variant?: 'default' | 'toolbar'
}

export function ThemeToggle({ className = '', variant = 'default' }: Props) {
  const { resolved, toggle } = useTheme()
  const isDark = resolved === 'dark'

  const baseToolbar =
    'inline-flex h-10 w-10 items-center justify-center rounded-xl border-0 bg-slate-200/80 text-slate-700 transition-all duration-200 hover:bg-blue-500/15 hover:text-blue-700 active:scale-95 dark:bg-slate-900/70 dark:text-slate-300 dark:hover:bg-cyan-500/10 dark:hover:text-cyan-200'

  return (
    <button
      type="button"
      onClick={toggle}
      title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      className={[
        variant === 'toolbar'
          ? baseToolbar
          : [
              'inline-flex h-10 w-10 items-center justify-center rounded-xl border transition-all duration-200',
              'border-zimon-border bg-zimon-card/80 text-zimon-fg hover:border-zimon-accent/50 hover:bg-zimon-panel active:scale-95',
              isDark
                ? 'shadow-[0_0_20px_-4px_rgba(34,211,238,0.35)] ring-1 ring-cyan-400/25 dark:border-cyan-500/30'
                : '',
            ].join(' '),
        className,
      ].join(' ')}
    >
      {isDark ? <Sun className="h-5 w-5 text-amber-300" /> : <Moon className="h-5 w-5 text-slate-600" />}
    </button>
  )
}
