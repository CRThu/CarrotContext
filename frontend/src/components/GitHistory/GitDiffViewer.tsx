import Editor from '@monaco-editor/react'

interface GitDiffViewerProps {
  oldContent: string
  newContent: string
  fileName: string
}

function getLanguageId(fileName: string): string {
  const ext = fileName.split('.').pop()?.toLowerCase() || ''
  const map: Record<string, string> = {
    py: 'python', js: 'javascript', ts: 'typescript',
    json: 'json', yaml: 'yaml', yml: 'yaml',
    md: 'markdown', markdown: 'markdown',
    html: 'html', css: 'css',
    sh: 'shell', bash: 'shell',
  }
  return map[ext] || 'plaintext'
}

export default function GitDiffViewer({ oldContent, newContent, fileName }: GitDiffViewerProps) {
  if (!oldContent && !newContent) {
    return (
      <div className="text-sm text-slate-400 dark:text-slate-500 py-4 text-center">
        没有差异
      </div>
    )
  }

  const language = getLanguageId(fileName)

  return (
    <div className="h-full">
      <Editor
        height="100%"
        language={language}
        original={oldContent}
        modified={newContent}
        theme="vs-dark"
        options={{
          renderSideBySide: true,
          readOnly: true,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          fontSize: 13,
          lineNumbers: 'on',
          renderLineHighlight: 'none',
          overviewRulerBorder: false,
          hideCursorInOverviewRuler: true,
          scrollbar: { vertical: 'auto', horizontal: 'auto' },
        }}
      />
    </div>
  )
}
