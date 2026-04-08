/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      colors: {
        zimon: {
          bg: 'var(--zimon-bg)',
          panel: 'var(--zimon-panel)',
          card: 'var(--zimon-card)',
          border: 'var(--zimon-border)',
          accent: 'var(--zimon-accent)',
          accent2: 'var(--zimon-accent2)',
          fg: 'var(--zimon-fg)',
          muted: 'var(--zimon-muted)',
        },
      },
      keyframes: {
        'auth-enter': {
          '0%': { opacity: '0', transform: 'translateY(18px) scale(0.985)' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'orb-glow': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.85' },
        },
        'ring-pulse': {
          '0%, 100%': {
            boxShadow:
              '0 0 28px rgba(34,211,238,0.4), inset 0 1px 0 rgba(255,255,255,0.25)',
          },
          '50%': {
            boxShadow:
              '0 0 52px rgba(34,211,238,0.75), inset 0 1px 0 rgba(255,255,255,0.3)',
          },
        },
        'float-fish': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        'dash-slow': {
          '0%': { strokeDashoffset: '0' },
          '100%': { strokeDashoffset: '-120' },
        },
        'dash-slower': {
          '0%': { strokeDashoffset: '0' },
          '100%': { strokeDashoffset: '-80' },
        },
      },
      animation: {
        'auth-enter': 'auth-enter 0.9s cubic-bezier(0.22, 1, 0.36, 1) forwards',
        'orb-glow': 'orb-glow 3.8s ease-in-out infinite',
        'ring-pulse': 'ring-pulse 3.2s ease-in-out infinite',
        'float-fish': 'float-fish 4.8s ease-in-out infinite',
        'dash-slow': 'dash-slow 22s linear infinite',
        'dash-slower': 'dash-slower 32s linear infinite',
      },
    },
  },
  plugins: [],
}
