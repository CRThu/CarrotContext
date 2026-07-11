import { useState, useEffect } from 'react'
import { api } from '../../lib/api'
import type { GitCommit } from '../../types'
import { GitCommit as GitCommitIcon, RefreshCw, RotateCcw } from 'lucide-react'
import GitDiffViewer from './GitDiffViewer'

interface GitHistoryProps {
  knowledgeId: string
}

export default function GitHistory({ knowledgeId }: GitHistoryProps) {
  const [commits, setCommits] = useState<GitCommit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedCommit, setSelectedCommit] = useState<GitCommit | null>(null)
  const [diff, setDiff] = useState<string>('')
  const [loadingDiff, setLoadingDiff] = useState(false)

  useEffect(() => {
    loadCommits()
  }, [knowledgeId])

  const loadCommits = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.git.log(knowledgeId, 50)
      setCommits(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载提交历史失败')
    } finally {
      setLoading(false)
    }
  }

  const handleSelectCommit = async (commit: GitCommit) => {
    setSelectedCommit(commit)
    setLoadingDiff(true)
    try {
      const result = await api.git.diff(knowledgeId, undefined, commit.hash)
      setDiff(result.diff)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取差异失败')
    } finally {
      setLoadingDiff(false)
    }
  }

  const handleRevert = async (commit: GitCommit) => {
    if (!confirm(`确定要回滚到提交 ${commit.hash.slice(0, 8)} 吗？`)) return
    try {
      await api.git.commit(knowledgeId, `Revert to ${commit.hash.slice(0, 8)}`)
      loadCommits()
      setSelectedCommit(null)
      setDiff('')
    } catch (err) {
      setError(err instanceof Error ? err.message : '回滚失败')
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
        <p className="text-sm text-slate-400 dark:text-slate-500">暂无提交历史</p>
      </div>
    )
  }

  return (
    <div className="flex h-full">
      {/* Commit list */}
      <div className="w-80 border-r border-slate-200 dark:border-slate-700 overflow-y-auto">
        <div className="p-3 border-b border-slate-100 dark:border-slate-700">
          <button
            onClick={loadCommits}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            刷新
          </button>
        </div>
        <div className="divide-y divide-slate-100 dark:divide-slate-700">
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
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                {commit.author}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Diff view */}
      <div className="flex-1 overflow-y-auto">
        {selectedCommit ? (
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-medium text-slate-900 dark:text-white">
                  {selectedCommit.message}
                </h3>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                  {selectedCommit.hash} - {selectedCommit.author} - {new Date(selectedCommit.date).toLocaleString('zh-CN')}
                </p>
              </div>
              <button
                onClick={() => handleRevert(selectedCommit)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50 rounded-lg transition-all"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                回滚
              </button>
            </div>
            {loadingDiff ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="w-4 h-4 animate-spin text-slate-400" />
              </div>
            ) : (
              <GitDiffViewer diff={diff} />
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full">
            <p className="text-sm text-slate-400 dark:text-slate-500">选择一个提交查看差异</p>
          </div>
        )}
      </div>
    </div>
  )
}
