import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeHighlight from 'rehype-highlight'

interface MarkdownViewerProps {
  content: string
}

export default function MarkdownViewer({ content }: MarkdownViewerProps) {
  return (
    <div className="prose prose-slate prose-lg max-w-none
      prose-headings:font-semibold prose-headings:text-slate-900
      prose-p:leading-relaxed prose-p:text-slate-700
      prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
      prose-code:text-slate-800 prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:text-sm prose-code:font-normal prose-code:before:content-none prose-code:after:content-none
      prose-pre:bg-slate-900 prose-pre:rounded-xl prose-pre:border prose-pre:border-slate-200
      prose-th:text-slate-600 prose-td:text-slate-700
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
                  <div className="absolute top-3 right-3 text-[10px] font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-md uppercase tracking-wider z-10">
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
              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="min-w-full divide-y divide-slate-200" {...props}>
                  {children}
                </table>
              </div>
            )
          },
          thead({ children, ...props }) {
            return <thead className="bg-slate-50" {...props}>{children}</thead>
          },
          th({ children, ...props }) {
            return (
              <th
                className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider"
                {...props}
              >
                {children}
              </th>
            )
          },
          td({ children, ...props }) {
            return (
              <td className="px-4 py-3 text-sm text-slate-700" {...props}>
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
