import { useId, useState } from 'react'
import { ZIMON_BRAND_HERO_URL, ZIMON_LOGO_URL } from '../../constants/branding'

function ZimonWordmark() {
  return (
    <h1 className="relative mt-5 flex items-center justify-center gap-0 text-4xl font-bold tracking-tight text-white drop-shadow-[0_2px_24px_rgba(0,0,0,0.4)] sm:text-5xl md:text-[3.25rem]">
      <span className="bg-gradient-to-b from-white to-slate-200 bg-clip-text text-transparent">ZIM</span>
      <span
        className="relative mx-0.5 inline-flex h-[0.82em] w-[0.82em] items-center justify-center rounded-full border-[3px] border-cyan-300/90 bg-gradient-to-br from-cyan-400/40 to-blue-900/60 text-[0.32em] leading-none text-cyan-100 shadow-[0_0_32px_rgba(34,211,238,0.55),inset_0_1px_0_rgba(255,255,255,0.25)] animate-ring-pulse"
        aria-hidden
      >
        <span className="absolute inset-1 rounded-full border border-white/20" />
        ●
      </span>
      <span className="bg-gradient-to-b from-white to-slate-200 bg-clip-text text-transparent">N</span>
    </h1>
  )
}

function LogoFallback() {
  return (
    <div
      className="relative flex h-full w-full items-center justify-center rounded-full border border-cyan-400/35 bg-gradient-to-br from-slate-900 via-[#0c2744] to-[#061525] shadow-[inset_0_1px_0_rgba(255,255,255,0.12)]"
      aria-hidden
    >
      <div className="absolute inset-0 rounded-full bg-[radial-gradient(circle_at_30%_30%,rgba(56,189,248,0.2),transparent_60%)]" />
      <span className="relative text-6xl opacity-[0.92] drop-shadow-[0_0_20px_rgba(56,189,248,0.4)] sm:text-7xl">
        🐟
      </span>
    </div>
  )
}

/** Decorative zebrafish chips (bottom-left). */
function BrandFishDecor() {
  return (
    <div className="pointer-events-none absolute bottom-5 left-4 z-[5] flex gap-3 sm:bottom-8 sm:left-6">
      <div
        className="animate-float-fish flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-500/20 bg-slate-950/40 text-2xl shadow-lg shadow-cyan-900/20 backdrop-blur-md sm:h-12 sm:w-12"
        style={{ animationDelay: '0s' }}
        aria-hidden
      >
        🐟
      </div>
      <div
        className="animate-float-fish flex h-10 w-10 items-center justify-center rounded-2xl border border-sky-500/15 bg-slate-950/35 text-xl shadow-lg shadow-blue-900/20 backdrop-blur-md sm:h-11 sm:w-11"
        style={{ animationDelay: '0.8s' }}
        aria-hidden
      >
        🐠
      </div>
    </div>
  )
}

function NeuralWaves({ uid }: { uid: string }) {
  return (
    <svg
      className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.22]"
      viewBox="0 0 400 600"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden
    >
      <defs>
        <linearGradient id={`${uid}-g1`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="rgb(34,211,238)" stopOpacity="0.5" />
          <stop offset="100%" stopColor="rgb(37,99,235)" stopOpacity="0.1" />
        </linearGradient>
      </defs>
      <path
        d="M0,120 C80,80 120,160 200,130 S320,90 400,140"
        fill="none"
        stroke={`url(#${uid}-g1)`}
        strokeWidth="0.6"
        className="animate-dash-slow"
      />
      <path
        d="M0,220 C100,180 150,280 280,240 S350,200 400,260"
        fill="none"
        stroke="rgba(56,189,248,0.15)"
        strokeWidth="0.5"
        className="animate-dash-slower"
      />
      <path
        d="M0,380 C120,340 180,420 300,380 S380,320 400,400"
        fill="none"
        stroke="rgba(96,165,250,0.12)"
        strokeWidth="0.45"
        className="animate-dash-slow"
      />
    </svg>
  )
}

export function PremiumBrandPanel() {
  const uid = useId().replace(/:/g, '')
  const [heroOk, setHeroOk] = useState(false)
  const [heroFailed, setHeroFailed] = useState(false)
  const [imgLoaded, setImgLoaded] = useState(false)
  const [imgFailed, setImgFailed] = useState(false)

  return (
    <div className="relative flex min-h-[300px] w-full flex-col items-center justify-center overflow-hidden bg-[#050b18] px-6 py-12 sm:min-h-[340px] sm:py-14 lg:min-h-0 lg:w-[46%] lg:max-w-none lg:rounded-none lg:py-10 rounded-t-[1.75rem] lg:rounded-l-[1.75rem] lg:rounded-tr-none">
      {!heroFailed ? (
        <>
          <img
            src={ZIMON_BRAND_HERO_URL}
            alt="ZIMON — Zebrafish Integrated Motion and Optical Neuroanalysis Chamber"
            className={`absolute inset-0 z-0 h-full w-full object-cover object-center transition-opacity duration-700 ${
              heroOk ? 'opacity-100' : 'opacity-0'
            }`}
            onLoad={() => setHeroOk(true)}
            onError={() => setHeroFailed(true)}
            decoding="async"
          />
          <div
            className="pointer-events-none absolute inset-0 z-[1] bg-gradient-to-t from-[#020617]/88 via-transparent to-[#050b18]/55"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute inset-0 z-[1] bg-[radial-gradient(ellipse_85%_65%_at_50%_35%,transparent_20%,rgba(2,6,23,0.35)_100%)]"
            aria-hidden
          />
        </>
      ) : null}

      {!heroOk || heroFailed ? (
        <>
          <div
            className="pointer-events-none absolute -left-20 top-0 h-64 w-64 rounded-full bg-cyan-400/15 blur-[100px]"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute -right-16 bottom-0 h-72 w-72 rounded-full bg-blue-600/20 blur-[110px]"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute left-1/2 top-0 h-px w-[80%] -translate-x-1/2 bg-gradient-to-r from-transparent via-cyan-400/25 to-transparent"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_90%_70%_at_50%_20%,rgba(56,189,248,0.14),transparent_50%)]"
            aria-hidden
          />
          <div
            className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#020617]/95 via-transparent to-transparent"
            aria-hidden
          />
        </>
      ) : null}

      {heroFailed ? <NeuralWaves uid={uid} /> : null}
      {heroFailed ? <BrandFishDecor /> : null}

      {heroFailed ? (
        <div className="relative z-10 flex max-w-md flex-col items-center text-center">
          <div className="relative mb-1 h-40 w-40 sm:h-48 sm:w-48">
            <div
              className="absolute -inset-3 rounded-full bg-cyan-400/10 blur-2xl animate-orb-glow"
              aria-hidden
            />
            <div
              className="absolute -inset-1 rounded-full border border-cyan-400/20 bg-slate-950/30 shadow-[0_0_60px_rgba(34,211,238,0.15)] backdrop-blur-sm"
              aria-hidden
            />
            {!imgFailed ? (
              <img
                src={ZIMON_LOGO_URL}
                alt=""
                width={192}
                height={192}
                className={`relative z-[1] mx-auto h-full w-full rounded-full object-contain p-1 transition-opacity duration-700 ${
                  imgLoaded ? 'opacity-100' : 'opacity-0'
                }`}
                onLoad={() => setImgLoaded(true)}
                onError={() => setImgFailed(true)}
              />
            ) : null}
            <div
              className={`absolute inset-0 z-0 overflow-hidden rounded-full transition-opacity duration-500 ${
                imgLoaded && !imgFailed ? 'opacity-0' : 'opacity-100'
              }`}
            >
              <LogoFallback />
            </div>
          </div>

          <ZimonWordmark />
          <p className="mt-4 max-w-[19rem] px-1 text-[9px] font-medium uppercase leading-relaxed tracking-[0.18em] text-slate-300/90 sm:max-w-md sm:text-[10px] sm:tracking-[0.22em]">
            Zebrafish Integrated <span className="font-semibold text-cyan-300">Motion</span> &amp;
            Optical Neuroanalysis Chamber
          </p>
        </div>
      ) : (
        <span className="sr-only">
          ZIMON — Zebrafish Integrated Motion and Optical Neuroanalysis Chamber
        </span>
      )}
    </div>
  )
}
