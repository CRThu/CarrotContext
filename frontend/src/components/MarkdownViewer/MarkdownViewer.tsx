import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeHighlight from 'rehype-highlight'

interface MarkdownViewerProps {
  content: string
}

export default function MarkdownViewer({ content }: MarkdownViewerProps) {
  return (
    <div className="prose prose-slate dark:prose-invert prose-lg max-w-none
      prose-headings:font-semibold prose-headings:text-slate-900 dark:prose-headings:text-white
      prose-p:leading-relaxed prose-p:text-slate-700 dark:prose-p:text-slate-300
      prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
      prose-code:text-slate-800 dark:prose-code:text-slate-200 prose-code:bg-slate-100 dark:prose-code:bg-slate-700 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:text-sm prose-code:font-normal prose-code:before:content-none prose-code:after:content-none
      prose-pre:rounded-xl prose-pre:border prose-pre:border-slate-200 dark:prose-pre:border-slate-700 prose-pre:bg-slate-50 dark:prose-pre:bg-slate-900
      prose-th:text-slate-600 dark:prose-th:text-slate-300 prose-td:text-slate-700 dark:prose-td:text-slate-300
    ">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const isInline = !match && !className
            if (isInline) {
              return (
                <code className={className} {...props}>
                  {children}
                </code>
              )
            }
            return (
              <div className="relative">
                {match && (
                  <div className="absolute top-3 right-3 text-[10px] font-medium text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-md uppercase tracking-wider z-10">
                    {match[1]}
                  </div>
                )}
                <code className={className} {...props}>
                  {children}
                </code>
              </div>
            )
          },
          table({ children, ...props }) {
            return (
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
                <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700" {...props}>
                  {children}
                </table>
              </div>
            )
          },
          thead({ children, ...props }) {
            return <thead className="bg-slate-50 dark:bg-slate-700" {...props}>{children}</thead>
          },
          th({ children, ...props }) {
            return (
              <th
                className="px-4 py-3 text-left text-xs font-medium text-slate-500 dark:text-slate-300 uppercase tracking-wider"
                {...props}
              >
                {children}
              </th>
            )
          },
          td({ children, ...props }) {
            return (
              <td className="px-4 py-3 text-sm text-slate-700 dark:text-slate-300" {...props}>
                {children}
              </td>
            )
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
