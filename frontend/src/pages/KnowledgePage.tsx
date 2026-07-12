import { useEffect, useState, useCallback, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useKnowledgeStore } from '../stores/knowledgeStore'
import { useToastStore } from '../stores/toastStore'
import { api } from '../lib/api'
import FileTree from '../components/FileTree/FileTree'
import MarkdownViewer from '../components/MarkdownViewer/MarkdownViewer'
import CodeEditor from '../components/CodeEditor/CodeEditor'
import GitHistory from '../components/GitHistory/GitHistory'
import GitDiffViewer from '../components/GitHistory/GitDiffViewer'
import type { FileContent, GitCommit } from '../types'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'
import { ArrowLeft, Save, X, Pencil, History, FolderTree, Settings, Upload } from 'lucide-react'
import { ThemeToggle } from '../components/ThemeToggle'

type SidebarTab = 'files' | 'history'

export default function KnowledgePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<FileContent | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')
  const [isDirty, setIsDirty] = useState(false)
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>('files')
  const [selectedCommit, setSelectedCommit] = useState<GitCommit | null>(null)
  const [diffContent, setDiffContent] = useState<{ oldContent: string; newContent: string; fileName: string } | null>(null)
  const [loadingDiff, setLoadingDiff] = useState(false)

  const currentKnowledge = useKnowledgeStore((state) => state.currentKnowledge)
  const setCurrentKnowledge = useKnowledgeStore((state) => state.setCurrentKnowledge)
  const fileTree = useKnowledgeStore((state) => state.fileTree)
  const setFileTree = useKnowledgeStore((state) => state.setFileTree)
  const addToast = useToastStore((s) => s.addToast)
  const dirtyRef = useRef(false)

  useEffect(() => {
    dirtyRef.current = isDirty
  }, [isDirty])

  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (dirtyRef.current) {
        e.preventDefault()
      }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [])

  useEffect(() => {
    if (id) {
      loadKnowledge(id)
      loadTree(id)
    }
  }, [id])

  const loadKnowledge = async (knowledgeId: string) => {
    try {
      const knowledge = await api.knowledge.get(knowledgeId)
      setCurrentKnowledge(knowledge)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const loadTree = async (knowledgeId: string) => {
    try {
      const tree = await api.knowledge.tree(knowledgeId)
      setFileTree(tree)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载目录失败')
    }
  }

  const handleFileSelect = async (path: string) => {
    if (!id) return
    if (isDirty && !confirm('有未保存的修改，是否放弃？')) return
    setSelectedFile(path)
    setIsEditing(false)
    setIsDirty(false)
    setSelectedCommit(null)
    setDiffContent(null)
    setSidebarTab('files')
    try {
      const content = await api.knowledge.file(id, path)
      setFileContent(content)
      setEditContent(content.content)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载文件失败')
    }
  }

  const handleSave = useCallback(async () => {
    if (!id || !selectedFile) return
    try {
      await api.knowledge.updateFile(id, selectedFile, editContent)
      setIsEditing(false)
      setIsDirty(false)
      addToast({ type: 'success', message: '保存成功' })
      handleFileSelect(selectedFile)
    } catch (err) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : '保存失败' })
    }
  }, [id, selectedFile, editContent])

  const handleCancel = () => {
    if (isDirty && !confirm('有未保存的修改，是否放弃？')) return
    setIsEditing(false)
    setIsDirty(false)
    if (fileContent) setEditContent(fileContent.content)
  }

  useKeyboardShortcuts({
    onSave: isEditing ? handleSave : undefined,
    onEscape: isEditing ? handleCancel : undefined,
  })

  const handleMove = async (sourcePath: string, destPath: string) => {
    if (!id) return
    try {
      await api.knowledge.moveFile(id, sourcePath, destPath)
      loadTree(id)
      if (selectedFile === sourcePath) {
        setSelectedFile(null)
        setFileContent(null)
      }
      addToast({ type: 'success', message: '移动成功' })
    } catch (err) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : '移动失败' })
    }
  }

  const handleSelectCommit = async (commit: GitCommit) => {
    if (!id || !selectedFile) return
    setSelectedCommit(commit)
    setLoadingDiff(true)
    try {
      const result = await api.git.fileAtCommit(id, commit.hash, selectedFile)
      setDiffContent({
        oldContent: result.content,
        newContent: fileContent?.content || '',
        fileName: selectedFile,
      })
    } catch {
      const diffResult = await api.git.diff(id, selectedFile, commit.hash)
      setDiffContent({
        oldContent: diffResult.diff,
        newContent: '',
        fileName: selectedFile,
      })
    } finally {
      setLoadingDiff(false)
    }
  }

  const handleUpload = async () => {
    if (!id) return
    const input = document.createElement('input')
    input.type = 'file'
    input.multiple = true
    input.onchange = async () => {
      const files = input.files
      if (!files) return
      for (const file of Array.from(files)) {
        try {
          await api.knowledge.uploadFile(id, file)
          addToast({ type: 'success', message: `上传 ${file.name} 成功` })
        } catch (err) {
          addToast({ type: 'error', message: err instanceof Error ? err.message : `上传 ${file.name} 失败` })
        }
      }
      loadTree(id)
    }
    input.click()
  }

  const isMarkdown = (path: string) => path.endsWith('.md') || path.endsWith('.markdown')

  const getLanguageLabel = (path: string) => {
    const ext = path.split('.').pop()?.toLowerCase()
    const langMap: Record<string, string> = {
      py: 'Python', js: 'JavaScript', ts: 'TypeScript',
      json: 'JSON', yaml: 'YAML', yml: 'YAML',
      md: 'Markdown', markdown: 'Markdown',
      c: 'C', h: 'C Header', cpp: 'C++',
      java: 'Java', go: 'Go', rs: 'Rust',
      sh: 'Shell', bash: 'Bash',
      html: 'HTML', css: 'CSS',
    }
    return langMap[ext || ''] || ext?.toUpperCase() || ''
  }

  const getLanguageId = (path: string) => {
    const ext = path.split('.').pop()?.toLowerCase()
    const langMap: Record<string, string> = {
      py: 'python', js: 'javascript', ts: 'typescript',
      json: 'json', yaml: 'yaml', yml: 'yaml',
      md: 'markdown', markdown: 'markdown',
      c: 'c', h: 'c', cpp: 'cpp',
      java: 'java', go: 'go', rs: 'rust',
      sh: 'shell', bash: 'shell',
      html: 'html', css: 'css',
    }
    return langMap[ext || ''] || 'plaintext'
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900">
        <div className="inline-flex items-center gap-2 text-sm text-slate-400">
          <div className="w-4 h-4 border-2 border-slate-300 dark:border-slate-600 border-t-blue-500 rounded-full animate-spin" />
          加载中...
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50 dark:bg-slate-900">
      <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-100 dark:border-slate-700 z-40 flex-shrink-0">
        <div className="px-4 py-3 flex items-center gap-4">
          <button
            onClick={() => {
              if (isDirty && !confirm('有未保存的修改，是否放弃？')) return
              navigate('/')
            }}
            className="flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            返回
          </button>
          <div className="w-px h-5 bg-slate-200 dark:bg-slate-600" />
          <h1 className="text-base font-semibold text-slate-900 dark:text-white truncate">
            {currentKnowledge?.name || id}
          </h1>
          <button
            onClick={() => navigate(`/knowledge/${id}/properties`)}
            className="flex items-center gap-1.5 px-2 py-1 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          >
            <Settings className="w-3.5 h-3.5" />
            属性
          </button>
          {sidebarTab === 'files' && (
            <div className="flex items-center gap-2 ml-auto">
              <button
                onClick={handleUpload}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-all"
              >
                <Upload className="w-3.5 h-3.5" />
                上传
              </button>
              {selectedFile && (
                isEditing ? (
                  <>
                    <button
                      onClick={handleSave}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-lg transition-all shadow-sm"
                    >
                      <Save className="w-3.5 h-3.5" />
                      保存
                    </button>
                    <button
                      onClick={handleCancel}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white transition-colors"
                    >
                      <X className="w-3.5 h-3.5" />
                      取消
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-lg transition-all"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                    编辑
                  </button>
                )
              )}
            </div>
          )}
          <ThemeToggle />
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-72 bg-white dark:bg-slate-800 border-r border-slate-200/60 dark:border-slate-700 flex flex-col overflow-hidden flex-shrink-0">
          <div className="flex border-b border-slate-100 dark:border-slate-700">
            <button
              onClick={() => setSidebarTab('files')}
              className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2.5 text-xs font-medium transition-colors ${
                sidebarTab === 'files'
                  ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <FolderTree className="w-4 h-4" />
              文件
            </button>
            <button
              onClick={() => setSidebarTab('history')}
              className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2.5 text-xs font-medium transition-colors ${
                sidebarTab === 'history'
                  ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <History className="w-4 h-4" />
              历史
            </button>
          </div>

          <div className="flex-1 overflow-hidden">
            {sidebarTab === 'files' ? (
              <div className="pt-4 px-3 h-full overflow-y-auto scrollbar-thin">
                <div className="mb-3 px-2">
                  <h2 className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">文件目录</h2>
                </div>
                <FileTree
                  tree={fileTree}
                  onSelect={handleFileSelect}
                  selectedPath={selectedFile}
                  knowledgeId={id}
                  onMove={handleMove}
                  canWrite={true}
                  onRefresh={() => id && loadTree(id)}
                />
              </div>
            ) : (
              <div className="h-full">
                {id && <GitHistory knowledgeId={id} selectedFile={selectedFile} onSelectCommit={handleSelectCommit} />}
              </div>
            )}
          </div>
        </aside>

        <main className="flex-1 overflow-y-auto bg-slate-50 dark:bg-slate-900">
          <div className="max-w-4xl mx-auto p-8 h-full">
            {selectedFile && sidebarTab === 'files' && (
              <nav className="flex items-center gap-1.5 text-xs text-slate-400 dark:text-slate-500 mb-6 animate-fade-in">
                <span className="text-slate-600 dark:text-slate-300 font-medium">{currentKnowledge?.name}</span>
                {selectedFile.split('/').map((part, i, arr) => (
                  <span key={i} className="flex items-center gap-1.5">
                    <span className="text-slate-300 dark:text-slate-600">/</span>
                    <span className={i === arr.length - 1 ? 'text-slate-600 dark:text-slate-300 font-medium' : ''}>{part}</span>
                  </span>
                ))}
              </nav>
            )}

            <div className={`bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-8 ${
              (isEditing && sidebarTab === 'files') || sidebarTab === 'history' ? 'h-[calc(100vh-180px)]' : 'min-h-[calc(100vh-180px)]'
            }`}>
              {error && (
                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 rounded-xl text-sm animate-slide-up">
                  {error}
                </div>
              )}

              {sidebarTab === 'files' && (
                !selectedFile ? (
                  <div className="flex flex-col items-center justify-center h-full min-h-[400px]">
                    <div className="w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-2xl flex items-center justify-center mb-4">
                      <svg className="w-8 h-8 text-slate-300 dark:text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                      </svg>
                    </div>
                    <p className="text-sm text-slate-400 dark:text-slate-500">选择一个文件查看内容</p>
                  </div>
                ) : isEditing ? (
                  <CodeEditor
                    content={editContent}
                    onChange={(v) => { setEditContent(v); setIsDirty(true) }}
                    language={isMarkdown(selectedFile) ? 'markdown' : getLanguageId(selectedFile)}
                    height="100%"
                  />
                ) : fileContent && isMarkdown(selectedFile) ? (
                  <MarkdownViewer content={fileContent.content} />
                ) : fileContent ? (
                  <div className="relative">
                    {getLanguageLabel(selectedFile) && (
                      <div className="absolute top-3 right-3 text-[10px] font-medium text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-md uppercase tracking-wider z-10">
                        {getLanguageLabel(selectedFile)}
                      </div>
                    )}
                    <pre className="bg-slate-100 dark:bg-slate-900 text-slate-800 dark:text-slate-100 p-6 rounded-xl overflow-x-auto text-sm font-mono leading-relaxed border border-slate-200 dark:border-slate-700">
                      {fileContent.content}
                    </pre>
                  </div>
                ) : null
              )}

              {sidebarTab === 'history' && (
                loadingDiff ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="w-4 h-4 border-2 border-slate-300 dark:border-slate-600 border-t-blue-500 rounded-full animate-spin" />
                  </div>
                ) : diffContent ? (
                  <GitDiffViewer
                    oldContent={diffContent.oldContent}
                    newContent={diffContent.newContent}
                    fileName={diffContent.fileName}
                  />
                ) : selectedCommit ? (
                  <div className="text-center py-12">
                    <p className="text-sm text-slate-400 dark:text-slate-500">
                      请先在文件 tab 选择一个文件，再查看该提交的差异
                    </p>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <History className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
                    <p className="text-sm text-slate-400 dark:text-slate-500">
                      在左侧选择查看提交历史
                    </p>
                  </div>
                )
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
