import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import CodeEditor from '../../src/components/CodeEditor/CodeEditor'

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange, language, options }: any) => (
    <div data-testid="monaco-editor">
      <div data-testid="editor-content">{value}</div>
      <div data-testid="editor-language">{language}</div>
      <div data-testid="editor-readonly">{String(options?.readOnly)}</div>
      <button onClick={() => onChange?.('new content')}>Change</button>
    </div>
  ),
}))

describe('CodeEditor', () => {
  it('renders editor with content', () => {
    const content = 'const x = 1;'
    render(<CodeEditor content={content} onChange={() => {}} />)
    expect(screen.getByTestId('editor-content')).toHaveTextContent(content)
  })

  it('renders with specified language', () => {
    render(<CodeEditor content="" onChange={() => {}} language="javascript" />)
    expect(screen.getByTestId('editor-language')).toHaveTextContent('javascript')
  })

  it('defaults to plaintext language', () => {
    render(<CodeEditor content="" onChange={() => {}} />)
    expect(screen.getByTestId('editor-language')).toHaveTextContent('plaintext')
  })

  it('supports readOnly mode', () => {
    render(<CodeEditor content="" onChange={() => {}} readOnly />)
    expect(screen.getByTestId('editor-readonly')).toHaveTextContent('true')
  })

  it('calls onChange when content changes', () => {
    const handleChange = vi.fn()
    render(<CodeEditor content="" onChange={handleChange} />)
    screen.getByText('Change').click()
    expect(handleChange).toHaveBeenCalledWith('new content')
  })
})
