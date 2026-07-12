import { useState, useRef, type JSX } from 'react'
import type { TreeNode } from '../../types'
import { api } from '../../lib/api'
import { useToastStore } from '../../stores/toastStore'
import ContextMenu from '../ContextMenu'
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
  Upload,
  FilePlus,
  FolderPlus,
  Trash2,
  Pencil,
} from 'lucide-react'

interface FileTreeProps {
  tree: TreeNode[]
  onSelect: (path: string) => void
  selectedPath: string | null
  knowledgeId?: string
  onMove?: (sourcePath: string, destPath: string) => void
  canWrite?: boolean
  onRefresh?: () => void
}

export default function FileTree({ tree, onSelect, selectedPath, knowledgeId, onMove, canWrite, onRefresh }: FileTreeProps) {
  return (
    <div className="py-1 px-1">
      {tree.map((node) => (
        <FileTreeItem
          key={node.path}
          node={node}
          onSelect={onSelect}
          selectedPath={selectedPath}
          depth={0}
          knowledgeId={knowledgeId}
          onMove={onMove}
          canWrite={canWrite}
          onRefresh={onRefresh}
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
  knowledgeId?: string
  onMove?: (sourcePath: string, destPath: string) => void
  canWrite?: boolean
  onRefresh?: () => void
}

function FileTreeItem({ node, onSelect, selectedPath, depth, knowledgeId, onMove, canWrite, onRefresh }: FileTreeItemProps) {
  const [expanded, setExpanded] = useState(false)
  const [isDragOver, setIsDragOver] = useState(false)
  const [isRenaming, setIsRenaming] = useState(false)
  const [renameValue, setRenameValue] = useState(node.name)
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const isSelected = selectedPath === node.path
  const paddingLeft = `${depth * 16 + 8}px`
  const addToast = useToastStore((s) => s.addToast)

  const handleClick = () => {
    if (node.is_dir) {
      setExpanded(!expanded)
    } else {
      onSelect(node.path)
    }
  }

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault()
    if (!knowledgeId) return
    setContextMenu({ x: e.clientX, y: e.clientY })
  }

  const handleRename = async () => {
    if (!knowledgeId || !renameValue.trim() || renameValue === node.name) {
      setIsRenaming(false)
      return
    }
    const parentPath = node.path.includes('/') ? node.path.slice(0, node.path.lastIndexOf('/')) : ''
    const newPath = parentPath ? `${parentPath}/${renameValue}` : renameValue
    try {
      await api.knowledge.moveFile(knowledgeId, node.path, newPath)
      addToast({ type: 'success', message: '重命名成功' })
      onRefresh?.()
    } catch (err) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : '重命名失败' })
    }
    setIsRenaming(false)
  }

  const handleDelete = async () => {
    if (!knowledgeId) return
    if (!confirm(`确定要删除 ${node.name} 吗？`)) return
    try {
      await api.knowledge.deleteFile(knowledgeId, node.path)
      addToast({ type: 'success', message: '删除成功' })
      onRefresh?.()
    } catch (err) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : '删除失败' })
    }
  }

  const handleUpload = async () => {
    if (!knowledgeId) return
    const input = document.createElement('input')
    input.type = 'file'
    input.multiple = true
    input.onchange = async () => {
      const files = input.files
      if (!files) return
      for (const file of Array.from(files)) {
        try {
          const uploadPath = node.is_dir ? node.path : node.path.slice(0, node.path.lastIndexOf('/'))
          await api.knowledge.uploadFile(knowledgeId, file, uploadPath)
          addToast({ type: 'success', message: `上传 ${file.name} 成功` })
        } catch (err) {
          addToast({ type: 'error', message: err instanceof Error ? err.message : `上传 ${file.name} 失败` })
        }
      }
      onRefresh?.()
    }
    input.click()
  }

  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.setData('text/plain', node.path)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent) => {
    if (node.is_dir) {
      e.preventDefault()
      e.dataTransfer.dropEffect = 'move'
      setIsDragOver(true)
    }
  }

  const handleDragLeave = () => setIsDragOver(false)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const sourcePath = e.dataTransfer.getData('text/plain')
    if (sourcePath && sourcePath !== node.path && onMove) {
      const destPath = node.is_dir ? `${node.path}/${sourcePath.split('/').pop()}` : node.path
      onMove(sourcePath, destPath)
    }
  }

  const contextItems = [
    ...(node.is_dir
      ? [
          { label: '上传文件', icon: <Upload className="w-4 h-4" />, onClick: handleUpload },
          { label: '新建文件', icon: <FilePlus className="w-4 h-4" />, onClick: () => {} },
          { label: '新建目录', icon: <FolderPlus className="w-4 h-4" />, onClick: () => {} },
        ]
      : [
          { label: '打开', icon: <FileText className="w-4 h-4" />, onClick: handleClick },
        ]),
    ...(canWrite
      ? [
          { label: '重命名', icon: <Pencil className="w-4 h-4" />, onClick: () => setIsRenaming(true) },
          { label: '删除', icon: <Trash2 className="w-4 h-4" />, onClick: handleDelete, danger: true },
        ]
      : []),
  ]

  return (
    <div>
      <div
        className={`flex items-center gap-2 py-1.5 px-2 rounded-lg cursor-pointer text-sm transition-colors group ${
          isSelected
            ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-medium'
            : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
        } ${isDragOver ? 'bg-blue-100 dark:bg-blue-800/40 ring-2 ring-blue-300 dark:ring-blue-600' : ''}`}
        style={{ paddingLeft }}
        onClick={handleClick}
        onContextMenu={handleContextMenu}
        draggable={!isRenaming}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {node.is_dir ? (
          <>
            <span className="flex-shrink-0">
              {expanded ? <ChevronDown className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" /> : <ChevronRight className="w-3.5 h-3.5 text-slate-400 dark:text-slate-500" />}
            </span>
            {expanded ? <FolderOpen className="w-4 h-4 text-blue-500 dark:text-blue-400 flex-shrink-0" /> : <Folder className="w-4 h-4 text-blue-500 dark:text-blue-400 flex-shrink-0" />}
          </>
        ) : (
          <>
            <span className="w-3.5" />
            {getFileIcon(node.name)}
          </>
        )}
        {isRenaming ? (
          <input
            ref={inputRef}
            value={renameValue}
            onChange={(e) => setRenameValue(e.target.value)}
            onBlur={handleRename}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleRename()
              if (e.key === 'Escape') setIsRenaming(false)
            }}
            className="flex-1 px-1 py-0 text-sm bg-white dark:bg-slate-700 border border-blue-500 rounded focus:outline-none"
            autoFocus
            onClick={(e) => e.stopPropagation()}
          />
        ) : (
          <span className="truncate">{node.name}</span>
        )}
      </div>
      {node.is_dir && expanded && node.children && (
        <div className="border-l border-slate-100 dark:border-slate-600 ml-4">
          {node.children.map((child) => (
            <FileTreeItem
              key={child.path}
              node={child}
              onSelect={onSelect}
              selectedPath={selectedPath}
              depth={depth + 1}
              knowledgeId={knowledgeId}
              onMove={onMove}
              canWrite={canWrite}
              onRefresh={onRefresh}
            />
          ))}
        </div>
      )}
      {contextMenu && (
        <ContextMenu
          items={contextItems}
          position={contextMenu}
          onClose={() => setContextMenu(null)}
        />
      )}
    </div>
  )
}

function getFileIcon(name: string): JSX.Element {
  if (name.endsWith('.md') || name.endsWith('.markdown')) {
    return <FileText className="w-4 h-4 text-slate-400 dark:text-slate-500 flex-shrink-0" />
  }
  if (name.endsWith('.py')) {
    return <FileCode className="w-4 h-4 text-green-500 dark:text-green-400 flex-shrink-0" />
  }
  if (name.endsWith('.js') || name.endsWith('.ts') || name.endsWith('.jsx') || name.endsWith('.tsx')) {
    return <FileCode className="w-4 h-4 text-yellow-500 dark:text-yellow-400 flex-shrink-0" />
  }
  if (name.endsWith('.json')) {
    return <FileJson className="w-4 h-4 text-orange-400 dark:text-orange-300 flex-shrink-0" />
  }
  if (name.endsWith('.yaml') || name.endsWith('.yml')) {
    return <FileCog className="w-4 h-4 text-purple-400 dark:text-purple-300 flex-shrink-0" />
  }
  return <File className="w-4 h-4 text-slate-400 dark:text-slate-500 flex-shrink-0" />
}
