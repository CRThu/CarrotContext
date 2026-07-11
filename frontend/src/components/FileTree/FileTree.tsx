import { useState, type JSX } from 'react'
import type { TreeNode } from '../../types'
import {
  Folder,
  FolderOpen,
  FileText,
  FileCode,
  FileJson,
  FileCog,
  File,
  ChevronRight,
  ChevronDown,
} from 'lucide-react'

interface FileTreeProps {
  tree: TreeNode[]
  onSelect: (path: string) => void
  selectedPath: string | null
}

export default function FileTree({ tree, onSelect, selectedPath }: FileTreeProps) {
  return (
    <div className="py-1 px-1">
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
        className={`flex items-center gap-2 py-1.5 px-2 rounded-lg cursor-pointer text-sm transition-colors ${
          isSelected
            ? 'bg-blue-50 text-blue-600 font-medium'
            : 'text-slate-600 hover:bg-slate-100'
        }`}
        style={{ paddingLeft }}
        onClick={handleClick}
      >
        {node.is_dir ? (
          <>
            <span className="flex-shrink-0">
              {expanded ? (
                <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
              ) : (
                <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              )}
            </span>
            {expanded ? (
              <FolderOpen className="w-4 h-4 text-blue-500 flex-shrink-0" />
            ) : (
              <Folder className="w-4 h-4 text-blue-500 flex-shrink-0" />
            )}
          </>
        ) : (
          <>
            <span className="w-3.5" />
            {getFileIcon(node.name)}
          </>
        )}
        <span className="truncate">{node.name}</span>
      </div>
      {node.is_dir && expanded && node.children && (
        <div className="border-l border-slate-100 ml-4">
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

function getFileIcon(name: string): JSX.Element {
  if (name.endsWith('.md') || name.endsWith('.markdown')) {
    return <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
  }
  if (name.endsWith('.py')) {
    return <FileCode className="w-4 h-4 text-green-500 flex-shrink-0" />
  }
  if (name.endsWith('.js') || name.endsWith('.ts') || name.endsWith('.jsx') || name.endsWith('.tsx')) {
    return <FileCode className="w-4 h-4 text-yellow-500 flex-shrink-0" />
  }
  if (name.endsWith('.json')) {
    return <FileJson className="w-4 h-4 text-orange-400 flex-shrink-0" />
  }
  if (name.endsWith('.yaml') || name.endsWith('.yml')) {
    return <FileCog className="w-4 h-4 text-purple-400 flex-shrink-0" />
  }
  return <File className="w-4 h-4 text-slate-400 flex-shrink-0" />
}
