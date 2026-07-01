import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MarkdownViewer from '../../src/components/MarkdownViewer/MarkdownViewer'

describe('MarkdownViewer', () => {
  it('renders markdown content', () => {
    render(<MarkdownViewer content="# Hello World" />)
    expect(screen.getByText('Hello World')).toBeInTheDocument()
  })

  it('renders bold text', () => {
    render(<MarkdownViewer content="**bold text**" />)
    expect(screen.getByText('bold text')).toBeInTheDocument()
  })

  it('renders links', () => {
    render(<MarkdownViewer content="[link](https://example.com)" />)
    expect(screen.getByText('link')).toHaveAttribute('href', 'https://example.com')
  })

  it('renders paragraphs', () => {
    render(<MarkdownViewer content="Hello World" />)
    expect(screen.getByText('Hello World')).toBeInTheDocument()
  })

  it('renders blockquotes', () => {
    render(<MarkdownViewer content="> quote" />)
    expect(screen.getByText('quote')).toBeInTheDocument()
  })
})
