import type { LucideIcon } from 'lucide-react'
import type { InputHTMLAttributes, ReactNode } from 'react'

type Props = {
  id: string
  label: string
  leftIcon: LucideIcon
  rightSlot?: ReactNode
} & Omit<InputHTMLAttributes<HTMLInputElement>, 'className'>

export function AuthTextField({
  id,
  label,
  leftIcon: LeftIcon,
  rightSlot,
  ...inputProps
}: Props) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-semibold text-slate-800">
        {label}
      </label>
      <div className="group relative mt-2">
        <LeftIcon
          className="pointer-events-none absolute left-3.5 top-1/2 z-[1] h-[1.125rem] w-[1.125rem] -translate-y-1/2 text-slate-500 transition-colors group-focus-within:text-[#1e3a5f]"
          aria-hidden
        />
        <input
          id={id}
          className={`w-full rounded-xl border border-slate-200 bg-slate-50 py-3.5 pl-11 text-[0.9375rem] text-slate-900 shadow-sm placeholder:text-slate-500 outline-none ring-0 transition-all duration-200 hover:border-slate-300 hover:bg-white focus:border-[#1e3a5f]/55 focus:bg-white focus:shadow-[0_0_0_3px_rgba(30,58,95,0.14)] ${
            rightSlot ? 'pr-11' : 'pr-4'
          }`}
          {...inputProps}
        />
        {rightSlot ? (
          <div className="absolute right-2 top-1/2 z-[1] -translate-y-1/2">{rightSlot}</div>
        ) : null}
      </div>
    </div>
  )
}
