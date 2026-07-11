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

  it('makes items draggable', () => {
    const onSelect = vi.fn()
    render(<FileTree tree={mockTree} onSelect={onSelect} selectedPath={null} />)
    const items = document.querySelectorAll('[draggable="true"]')
    expect(items.length).toBe(2)
    items.forEach((item) => {
      expect(item).toHaveAttribute('draggable', 'true')
    })
  })

  it('calls onMove when file is dropped on folder', () => {
    const onSelect = vi.fn()
    const onMove = vi.fn()
    render(<FileTree tree={mockTree} onSelect={onSelect} selectedPath={null} onMove={onMove} />)

    const folder = screen.getByText('src')
    const file = screen.getByText('README.md')

    // Simulate drag and drop
    const dragStartEvent = new Event('dragstart', { bubbles: true })
    Object.defineProperty(dragStartEvent, 'dataTransfer', {
      value: { setData: vi.fn(), effectAllowed: '' },
    })
    fireEvent(file, dragStartEvent)

    const dropEvent = new Event('drop', { bubbles: true })
    Object.defineProperty(dropEvent, 'dataTransfer', {
      value: {
        getData: vi.fn().mockReturnValue('README.md'),
        preventDefault: vi.fn(),
      },
    })
    fireEvent(folder, dropEvent)

    expect(onMove).toHaveBeenCalledWith('README.md', 'src/README.md')
  })
})
