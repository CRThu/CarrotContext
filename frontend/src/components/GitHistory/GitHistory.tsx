import { useState, useEffect } from 'react'
import { api } from '../../lib/api'
import type { GitCommit } from '../../types'
import { GitCommit as GitCommitIcon, RefreshCw, RotateCcw, GitBranch } from 'lucide-react'
import { useToastStore } from '../../stores/toastStore'

interface GitHistoryProps {
  knowledgeId: string
  selectedFile?: string | null
  onSelectCommit?: (commit: GitCommit) => void
}

export default function GitHistory({ knowledgeId, selectedFile, onSelectCommit }: GitHistoryProps) {
  const [commits, setCommits] = useState<GitCommit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCommit, setSelectedCommit] = useState<GitCommit | null>(null)
  const addToast = useToastStore((s) => s.addToast)

  useEffect(() => {
    loadCommits()
  }, [knowledgeId, selectedFile])

  const loadCommits = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.git.log(knowledgeId, 50, selectedFile || undefined)
      setCommits(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载提交历史失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectCommit = (commit: GitCommit) => {
    setSelectedCommit(commit)
    onSelectCommit?.(commit)
  }

  const handleRevert = async (commit: GitCommit) => {
    if (!confirm(`确定要回滚到提交 ${commit.hash.slice(0, 8)} 吗？`)) return
    try {
      await api.git.revert(knowledgeId, commit.hash)
      addToast({ type: 'success', message: '回滚成功' })
      loadCommits()
      setSelectedCommit(null)
    } catch (err) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : '回滚失败' })
    }
  }

  const handleInit = async () => {
    try {
      await api.git.init(knowledgeId)
      addToast({ type: 'success', message: 'Git 初始化成功' })
      loadCommits()
    } catch (err) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : '初始化失败' })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="inline-flex items-center gap-2 text-sm text-slate-400">
          <RefreshCw className="w-4 h-4 animate-spin" />
          加载中...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 rounded-xl text-sm">
        {error}
      </div>
    )
  }

  if (commits.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <GitCommitIcon className="w-12 h-12 text-slate-300 dark:text-slate-600 mb-3" />
        <p className="text-sm text-slate-400 dark:text-slate-500 mb-4">暂无提交历史</p>
        <button
          onClick={handleInit}
          className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl transition-all shadow-sm"
        >
          <GitBranch className="w-4 h-4" />
          初始化 Git 仓库
        </button>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-3 border-b border-slate-100 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <button
            onClick={loadCommits}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            刷新
          </button>
          {selectedFile && (
            <span className="text-xs text-slate-400 dark:text-slate-500 truncate max-w-[150px]">
              {selectedFile}
            </span>
          )}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700">
        {commits.map((commit) => (
          <button
            key={commit.hash}
            onClick={() => handleSelectCommit(commit)}
            className={`w-full text-left p-3 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors ${
              selectedCommit?.hash === commit.hash ? 'bg-blue-50 dark:bg-blue-900/30' : ''
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-mono text-slate-400 dark:text-slate-500">
                {commit.hash.slice(0, 8)}
              </span>
              <span className="text-xs text-slate-400 dark:text-slate-500">
                {new Date(commit.date).toLocaleDateString('zh-CN')}
              </span>
            </div>
            <p className="text-sm text-slate-700 dark:text-slate-200 truncate">
              {commit.message}
            </p>
            <div className="flex items-center justify-between mt-1">
              <p className="text-xs text-slate-400 dark:text-slate-500">
                {commit.author}
              </p>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  handleRevert(commit)
                }}
                className="p-1 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-all"
                title="回滚"
              >
                <RotateCcw className="w-3 h-3" />
              </button>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
