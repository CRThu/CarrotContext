import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import GitDiffViewer from '../../src/components/GitHistory/GitDiffViewer'

describe('GitDiffViewer', () => {
  it('renders diff content', () => {
    const diff = '+added line\n-removed line'
    render(<GitDiffViewer diff={diff} />)
    expect(screen.getByText('+added line')).toBeInTheDocument()
    expect(screen.getByText('-removed line')).toBeInTheDocument()
  })

  it('shows empty message when no diff', () => {
    render(<GitDiffViewer diff="" />)
    expect(screen.getByText('没有差异')).toBeInTheDocument()
  })

  it('colors added lines green', () => {
    const diff = '+new content'
    render(<GitDiffViewer diff={diff} />)
    const element = screen.getByText('+new content')
    expect(element.className).toContain('text-green-400')
  })

  it('colors removed lines red', () => {
    const diff = '-old content'
    render(<GitDiffViewer diff={diff} />)
    const element = screen.getByText('-old content')
    expect(element.className).toContain('text-red-400')
  })

  it('colors hunk headers blue', () => {
    const diff = '@@ -1,3 +1,4 @@'
    render(<GitDiffViewer diff={diff} />)
    const element = screen.getByText('@@ -1,3 +1,4 @@')
    expect(element.className).toContain('text-blue-400')
  })

  it('renders multiple diff lines', () => {
    const diff = 'line1\nline2\nline3'
    render(<GitDiffViewer diff={diff} />)
    expect(screen.getByText('line1')).toBeInTheDocument()
    expect(screen.getByText('line2')).toBeInTheDocument()
    expect(screen.getByText('line3')).toBeInTheDocument()
  })
})
