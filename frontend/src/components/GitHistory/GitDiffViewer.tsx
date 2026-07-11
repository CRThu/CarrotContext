interface GitDiffViewerProps {
  diff: string
}

export default function GitDiffViewer({ diff }: GitDiffViewerProps) {
  if (!diff) {
    return (
      <div className="text-sm text-slate-400 dark:text-slate-500 py-4">
        没有差异
      </div>
    )
  }

  const lines = diff.split('\n')

  return (
    <pre className="bg-slate-100 dark:bg-slate-900 text-slate-800 dark:text-slate-100 p-4 rounded-xl overflow-x-auto text-sm font-mono leading-relaxed border border-slate-200 dark:border-slate-700">
      {lines.map((line, i) => {
        let className = ''
        if (line.startsWith('+') && !line.startsWith('+++')) {
          className = 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20'
        } else if (line.startsWith('-') && !line.startsWith('---')) {
          className = 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20'
        } else if (line.startsWith('@@')) {
          className = 'text-blue-600 dark:text-blue-400'
        } else if (line.startsWith('diff') || line.startsWith('index') || line.startsWith('---') || line.startsWith('+++')) {
          className = 'text-slate-500 dark:text-slate-400'
        }

        return (
          <div key={i} className={`${className} px-2 -mx-2`}>
            {line}
          </div>
        )
      })}
    </pre>
  )
}
