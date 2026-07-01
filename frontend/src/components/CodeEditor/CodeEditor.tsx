import Editor from '@monaco-editor/react'

interface CodeEditorProps {
  content: string
  onChange: (value: string) => void
  language?: string
  readOnly?: boolean
  height?: string
}

export default function CodeEditor({
  content,
  onChange,
  language = 'plaintext',
  readOnly = false,
  height = '100%',
}: CodeEditorProps) {
  const handleChange = (value: string | undefined) => {
    if (value !== undefined) {
      onChange(value)
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 overflow-hidden shadow-sm" style={{ height }}>
      <Editor
        height="100%"
        language={language}
        value={content}
        onChange={handleChange}
        options={{
          readOnly,
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          automaticLayout: true,
          tabSize: 2,
        }}
      />
    </div>
  )
}
