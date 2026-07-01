import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useKnowledgeStore } from '../stores/knowledgeStore'
import { api } from '../lib/api'
import FileTree from '../components/FileTree/FileTree'
import MarkdownViewer from '../components/MarkdownViewer/MarkdownViewer'
import CodeEditor from '../components/CodeEditor/CodeEditor'
import type { FileContent } from '../types'
import { ArrowLeft, Save, X, Pencil } from 'lucide-react'

export default function KnowledgePage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileContent, setFileContent] = useState<FileContent | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState('')

  const currentKnowledge = useKnowledgeStore((state) => state.currentKnowledge)
  const setCurrentKnowledge = useKnowledgeStore((state) => state.setCurrentKnowledge)
  const fileTree = useKnowledgeStore((state) => state.fileTree)
  const setFileTree = useKnowledgeStore((state) => state.setFileTree)

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
    setSelectedFile(path)
    try {
      const content = await api.knowledge.file(id, path)
      setFileContent(content)
      setEditContent(content.content)
      setIsEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : '加载文件失败')
    }
  }

  const handleSave = async () => {
    if (!id || !selectedFile) return
    try {
      await api.knowledge.updateFile(id, selectedFile, editContent)
      setIsEditing(false)
      handleFileSelect(selectedFile)
    } catch (err) {
      setError(err instanceof Error ? err.message : '保存失败')
    }
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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="inline-flex items-center gap-2 text-sm text-slate-400">
          <div className="w-4 h-4 border-2 border-slate-300 border-t-blue-500 rounded-full animate-spin" />
          加载中...
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-100 z-40 flex-shrink-0">
        <div className="px-4 py-3 flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-800 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            返回
          </button>
          <div className="w-px h-5 bg-slate-200" />
          <h1 className="text-base font-semibold text-slate-900 truncate">
            {currentKnowledge?.name || id}
          </h1>
          {selectedFile && (
            <div className="flex items-center gap-2 ml-auto">
              {isEditing ? (
                <>
                  <button
                    onClick={handleSave}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-lg transition-all shadow-sm"
                  >
                    <Save className="w-3.5 h-3.5" />
                    保存
                  </button>
                  <button
                    onClick={() => setIsEditing(false)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                    取消
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition-all"
                >
                  <Pencil className="w-3.5 h-3.5" />
                  编辑
                </button>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Two-column layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-72 bg-white border-r border-slate-200/60 flex flex-col overflow-hidden flex-shrink-0">
          <div className="pt-4 px-3 flex-1 overflow-y-auto scrollbar-thin">
            <div className="mb-3 px-2">
              <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">文件目录</h2>
            </div>
            <FileTree tree={fileTree} onSelect={handleFileSelect} selectedPath={selectedFile} />
          </div>
        </aside>

        {/* Canvas */}
        <main className="flex-1 overflow-y-auto bg-slate-50">
          <div className="max-w-4xl mx-auto p-8 h-full">
            {/* Breadcrumb */}
            {selectedFile && (
              <nav className="flex items-center gap-1.5 text-xs text-slate-400 mb-6 animate-fade-in">
                <span className="text-slate-600 font-medium">{currentKnowledge?.name}</span>
                {selectedFile.split('/').map((part, i, arr) => (
                  <span key={i} className="flex items-center gap-1.5">
                    <span className="text-slate-300">/</span>
                    <span className={i === arr.length - 1 ? 'text-slate-600 font-medium' : ''}>
                      {part}
                    </span>
                  </span>
                ))}
              </nav>
            )}

            {/* Content Canvas Card */}
            <div className={`bg-white rounded-2xl border border-slate-100 shadow-sm p-8 ${isEditing ? 'h-[calc(100vh-180px)]' : 'min-h-[calc(100vh-180px)]'}`}>
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-600 rounded-xl text-sm animate-slide-up">
                  {error}
                </div>
              )}

              {!selectedFile ? (
                <div className="flex flex-col items-center justify-center h-full min-h-[400px]">
                  <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                    </svg>
                  </div>
                  <p className="text-sm text-slate-400">选择一个文件查看内容</p>
                </div>
              ) : isEditing ? (
                <CodeEditor
                  content={editContent}
                  onChange={setEditContent}
                  language={isMarkdown(selectedFile) ? 'markdown' : 'plaintext'}
                  height="100%"
                />
              ) : fileContent && isMarkdown(selectedFile) ? (
                <MarkdownViewer content={fileContent.content} />
              ) : fileContent ? (
                <div className="relative">
                  {getLanguageLabel(selectedFile) && (
                    <div className="absolute top-3 right-3 text-[10px] font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md uppercase tracking-wider z-10">
                      {getLanguageLabel(selectedFile)}
                    </div>
                  )}
                  <pre className="bg-slate-900 text-slate-100 p-6 rounded-xl overflow-x-auto text-sm font-mono leading-relaxed">
                    {fileContent.content}
                  </pre>
                </div>
              ) : null}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
