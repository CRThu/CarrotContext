import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import FileTree from '../../src/components/FileTree/FileTree'

const mockTree = [
  {
    name: 'src',
    path: 'src',
    is_dir: true,
    children: [
      { name: 'main.py', path: 'src/main.py', is_dir: false },
      { name: 'utils.py', path: 'src/utils.py', is_dir: false },
    ],
  },
  { name: 'README.md', path: 'README.md', is_dir: false },
]

describe('FileTree', () => {
  it('renders file tree items', () => {
    const onSelect = vi.fn()
    render(<FileTree tree={mockTree} onSelect={onSelect} selectedPath={null} />)
    expect(screen.getByText('src')).toBeInTheDocument()
    expect(screen.getByText('README.md')).toBeInTheDocument()
  })

  it('expands directory on click', () => {
    const onSelect = vi.fn()
    render(<FileTree tree={mockTree} onSelect={onSelect} selectedPath={null} />)
    fireEvent.click(screen.getByText('src'))
    expect(screen.getByText('main.py')).toBeInTheDocument()
    expect(screen.getByText('utils.py')).toBeInTheDocument()
  })

  it('calls onSelect when file is clicked', () => {
    const onSelect = vi.fn()
    render(<FileTree tree={mockTree} onSelect={onSelect} selectedPath={null} />)
    fireEvent.click(screen.getByText('README.md'))
    expect(onSelect).toHaveBeenCalledWith('README.md')
  })
})
