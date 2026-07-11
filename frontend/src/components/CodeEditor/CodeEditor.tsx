import Editor from '@monaco-editor/react'
import { useThemeStore } from '../../stores/themeStore'

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
  const resolvedTheme = useThemeStore((state) => state.resolvedTheme)

  const handleChange = (value: string | undefined) => {
    if (value !== undefined) {
      onChange(value)
    }
  }

  return (
    <div className={`rounded-xl border overflow-hidden shadow-sm ${resolvedTheme === 'dark' ? 'border-slate-600' : 'border-slate-200'}`} style={{ height }}>
      <Editor
        height="100%"
        language={language}
        value={content}
        onChange={handleChange}
        theme={resolvedTheme === 'dark' ? 'vs-dark' : 'vs'}
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
