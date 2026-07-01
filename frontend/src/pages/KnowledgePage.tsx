import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useKnowledgeStore } from '../stores/knowledgeStore'
import { api } from '../lib/api'
import FileTree from '../components/FileTree/FileTree'
import MarkdownViewer from '../components/MarkdownViewer/MarkdownViewer'
import CodeEditor from '../components/CodeEditor/CodeEditor'
import type { FileContent } from '../types'

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

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">加载中...</div>
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-full mx-auto px-4 py-3 flex items-center gap-4">
          <button
            onClick={() => navigate('/')}
            className="text-gray-600 hover:text-gray-900"
          >
            ← 返回
          </button>
          <h1 className="text-xl font-semibold text-gray-900">
            {currentKnowledge?.name || id}
          </h1>
          {selectedFile && (
            <div className="flex items-center gap-2 ml-auto">
              {isEditing ? (
                <>
                  <button
                    onClick={handleSave}
                    className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                  >
                    保存
                  </button>
                  <button
                    onClick={() => setIsEditing(false)}
                    className="px-3 py-1 text-gray-600 text-sm hover:text-gray-900"
                  >
                    取消
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded hover:bg-gray-200"
                >
                  编辑
                </button>
              )}
            </div>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        <aside className="w-64 bg-white border-r overflow-y-auto">
          <FileTree tree={fileTree} onSelect={handleFileSelect} selectedPath={selectedFile} />
        </aside>

        <main className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          {!selectedFile ? (
            <div className="text-center text-gray-500 py-12">
              选择一个文件查看内容
            </div>
          ) : isEditing ? (
            <CodeEditor
              content={editContent}
              onChange={setEditContent}
              language={isMarkdown(selectedFile) ? 'markdown' : 'plaintext'}
            />
          ) : fileContent && isMarkdown(selectedFile) ? (
            <MarkdownViewer content={fileContent.content} />
          ) : fileContent ? (
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
              {fileContent.content}
            </pre>
          ) : null}
        </main>
      </div>
    </div>
  )
}
