import type { ReactNode } from 'react'

type Props = {
  brand: ReactNode
  children: ReactNode
  /** When set (e.g. login), hardware strip is pinned to the bottom of the right (login) column */
  footer?: ReactNode
}

/**
 * Full-viewport backdrop + centered card. Left column is image-only (full height). Optional `footer`
 * renders at the bottom of the right column under the form. Equal column heights on lg via flex stretch.
 */
export function AuthPremiumShell({ brand, children, footer }: Props) {
  return (
    <div className="relative min-h-screen overflow-x-hidden bg-zimon-bg font-sans text-zimon-fg dark:bg-[#030712] dark:text-slate-200">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_100%_70%_at_50%_-10%,rgba(37,99,235,0.14),transparent_58%)] dark:bg-[radial-gradient(ellipse_100%_70%_at_50%_-10%,rgba(30,58,138,0.35),transparent_55%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_55%_45%_at_100%_100%,rgba(59,130,246,0.1),transparent_50%)] dark:bg-[radial-gradient(ellipse_60%_50%_at_100%_100%,rgba(14,116,144,0.12),transparent_45%)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.14] mix-blend-multiply dark:opacity-[0.35] dark:mix-blend-overlay"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.06'/%3E%3C/svg%3E")`,
        }}
        aria-hidden
      />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-3 py-8 sm:px-4 sm:py-10 md:px-6 md:py-14">
        <div className="auth-card-enter flex w-full max-w-[1040px] min-h-0 flex-col overflow-hidden rounded-[1.75rem] border border-slate-200/90 bg-white text-slate-900 shadow-[0_24px_80px_-28px_rgba(15,23,42,0.18),0_0_0_1px_rgba(15,23,42,0.04)] dark:border-white/[0.08] dark:shadow-[0_32px_100px_-20px_rgba(0,0,0,0.65),0_0_0_1px_rgba(255,255,255,0.05)_inset]">
          <div className="flex min-h-0 flex-1 flex-col lg:min-h-[400px] lg:flex-row lg:items-stretch">
            {/* Left: hero / brand only — full column height for image */}
            <div className="flex min-h-0 w-full min-w-0 flex-col self-stretch lg:w-[46%] lg:flex-shrink-0">
              <div className="relative flex min-h-[170px] flex-1 flex-col overflow-hidden rounded-t-[1.75rem] sm:min-h-[200px] lg:h-full lg:min-h-0 lg:flex-1 lg:rounded-bl-[1.75rem] lg:rounded-tl-[1.75rem] lg:rounded-tr-none">
                {brand}
              </div>
            </div>
            {/* Right: form (centered) + optional hardware strip at bottom */}
            <div className="flex h-full min-h-0 min-w-0 flex-1 flex-col self-stretch rounded-b-[1.75rem] bg-white text-slate-900 lg:rounded-br-[1.75rem] lg:rounded-tr-[1.75rem]">
              <div className="flex min-h-0 w-full flex-1 flex-col items-center justify-center">
                {children}
              </div>
              {footer ? <div className="w-full shrink-0">{footer}</div> : null}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
