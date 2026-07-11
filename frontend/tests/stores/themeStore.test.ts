import { describe, it, expect, beforeEach } from 'vitest'
import { useThemeStore } from '../../src/stores/themeStore'

describe('themeStore', () => {
  beforeEach(() => {
    useThemeStore.setState({ resolvedTheme: 'light' })
    document.documentElement.classList.remove('dark')
  })

  it('has default resolvedTheme', () => {
    const state = useThemeStore.getState()
    expect(['light', 'dark']).toContain(state.resolvedTheme)
  })

  it('toggleTheme switches from light to dark', () => {
    useThemeStore.setState({ resolvedTheme: 'light' })
    useThemeStore.getState().toggleTheme()
    expect(useThemeStore.getState().resolvedTheme).toBe('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('toggleTheme switches from dark to light', () => {
    useThemeStore.setState({ resolvedTheme: 'dark' })
    document.documentElement.classList.add('dark')
    useThemeStore.getState().toggleTheme()
    expect(useThemeStore.getState().resolvedTheme).toBe('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('applies dark class when toggling to dark', () => {
    useThemeStore.setState({ resolvedTheme: 'light' })
    useThemeStore.getState().toggleTheme()
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('removes dark class when toggling to light', () => {
    document.documentElement.classList.add('dark')
    useThemeStore.setState({ resolvedTheme: 'dark' })
    useThemeStore.getState().toggleTheme()
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
