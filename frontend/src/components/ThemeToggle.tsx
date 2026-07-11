import { Moon, Sun } from 'lucide-react'
import { useThemeStore } from '../stores/themeStore'

export function ThemeToggle() {
  const { resolvedTheme, toggleTheme } = useThemeStore()

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors"
      title={resolvedTheme === 'dark' ? '切换到浅色模式' : '切换到深色模式'}
    >
      {resolvedTheme === 'dark' ? (
        <Moon className="w-5 h-5 text-blue-400" />
      ) : (
        <Sun className="w-5 h-5 text-amber-500" />
      )}
    </button>
  )
}
