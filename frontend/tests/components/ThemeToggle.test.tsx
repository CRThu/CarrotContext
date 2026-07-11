import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeToggle } from '../../src/components/ThemeToggle'
import { useThemeStore } from '../../src/stores/themeStore'

describe('ThemeToggle', () => {
  beforeEach(() => {
    useThemeStore.setState({ resolvedTheme: 'light' })
    document.documentElement.classList.remove('dark')
  })

  it('renders the theme toggle button', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
  })

  it('shows dark icon with light-to-dark title when theme is light', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('title', '切换到深色模式')
  })

  it('shows light icon with dark-to-light title when theme is dark', () => {
    useThemeStore.setState({ resolvedTheme: 'dark' })
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('title', '切换到浅色模式')
  })

  it('toggles from light to dark on click', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    expect(button).toHaveAttribute('title', '切换到浅色模式')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('toggles from dark to light on click', () => {
    useThemeStore.setState({ resolvedTheme: 'dark' })
    document.documentElement.classList.add('dark')
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    expect(button).toHaveAttribute('title', '切换到深色模式')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('applies dark class when toggling to dark mode', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('removes dark class when toggling to light mode', () => {
    document.documentElement.classList.add('dark')
    useThemeStore.setState({ resolvedTheme: 'dark' })
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    fireEvent.click(button)
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
