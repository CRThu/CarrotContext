import { useEffect } from 'react'

interface Shortcuts {
  onSave?: () => void
  onEscape?: () => void
}

export function useKeyboardShortcuts({ onSave, onEscape }: Shortcuts) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const isMod = e.metaKey || e.ctrlKey
      if (isMod && e.key === 's') {
        e.preventDefault()
        onSave?.()
      }
      if (e.key === 'Escape') {
        onEscape?.()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onSave, onEscape])
}
