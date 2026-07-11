import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface ThemeState {
  resolvedTheme: 'light' | 'dark'
  toggleTheme: () => void
}

function getSystemTheme(): 'light' | 'dark' {
  if (typeof window === 'undefined' || !window.matchMedia) return 'light'
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function applyTheme(resolvedTheme: 'light' | 'dark') {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  if (resolvedTheme === 'dark') {
    root.classList.add('dark')
  } else {
    root.classList.remove('dark')
  }
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      resolvedTheme: getSystemTheme(),
      toggleTheme: () => {
        const next = get().resolvedTheme === 'dark' ? 'light' : 'dark'
        applyTheme(next)
        set({ resolvedTheme: next })
      },
    }),
    {
      name: 'theme-storage',
      onRehydrateStorage: () => {
        return (state) => {
          const resolved = state?.resolvedTheme ?? getSystemTheme()
          applyTheme(resolved)
          if (state) state.resolvedTheme = resolved
        }
      },
    }
  )
)
