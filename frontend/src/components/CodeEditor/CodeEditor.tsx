import Editor from '@monaco-editor/react'

interface CodeEditorProps {
  content: string
  onChange: (value: string) => void
  language?: string
  readOnly?: boolean
}

export default function CodeEditor({
  content,
  onChange,
  language = 'plaintext',
  readOnly = false,
}: CodeEditorProps) {
  const handleChange = (value: string | undefined) => {
    if (value !== undefined) {
      onChange(value)
    }
  }

  return (
    <div className="h-full border rounded-lg overflow-hidden">
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
