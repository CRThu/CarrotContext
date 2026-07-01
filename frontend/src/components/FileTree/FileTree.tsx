import { useState } from 'react'
import type { TreeNode } from '../../types'

interface FileTreeProps {
  tree: TreeNode[]
  onSelect: (path: string) => void
  selectedPath: string | null
}

export default function FileTree({ tree, onSelect, selectedPath }: FileTreeProps) {
  return (
    <div className="py-2">
      {tree.map((node) => (
        <FileTreeItem
          key={node.path}
          node={node}
          onSelect={onSelect}
          selectedPath={selectedPath}
          depth={0}
        />
      ))}
    </div>
  )
}

interface FileTreeItemProps {
  node: TreeNode
  onSelect: (path: string) => void
  selectedPath: string | null
  depth: number
}

function FileTreeItem({ node, onSelect, selectedPath, depth }: FileTreeItemProps) {
  const [expanded, setExpanded] = useState(false)
  const isSelected = selectedPath === node.path
  const paddingLeft = `${depth * 16 + 8}px`

  const handleClick = () => {
    if (node.is_dir) {
      setExpanded(!expanded)
    } else {
      onSelect(node.path)
    }
  }

  return (
    <div>
      <div
        className={`flex items-center py-1 px-2 cursor-pointer hover:bg-gray-100 ${
          isSelected ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
        }`}
        style={{ paddingLeft }}
        onClick={handleClick}
      >
        <span className="mr-2 text-sm">
          {node.is_dir ? (expanded ? '📂' : '📁') : getFileIcon(node.name)}
        </span>
        <span className="text-sm truncate">{node.name}</span>
      </div>
      {node.is_dir && expanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeItem
              key={child.path}
              node={child}
              onSelect={onSelect}
              selectedPath={selectedPath}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function getFileIcon(name: string): string {
  if (name.endsWith('.md')) return '📝'
  if (name.endsWith('.py')) return '🐍'
  if (name.endsWith('.js') || name.endsWith('.ts')) return '📜'
  if (name.endsWith('.json')) return '📋'
  if (name.endsWith('.yaml') || name.endsWith('.yml')) return '⚙️'
  return '📄'
}
