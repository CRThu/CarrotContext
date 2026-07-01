import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import rehypeHighlight from 'rehype-highlight'

interface MarkdownViewerProps {
  content: string
}

export default function MarkdownViewer({ content }: MarkdownViewerProps) {
  return (
    <div className="prose prose-lg max-w-none">
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
                <div className="absolute top-2 right-2 text-xs text-gray-500 bg-gray-700 px-2 py-1 rounded">
                  {match ? match[1] : ''}
                </div>
                <code className={className} {...props}>
                  {children}
                </code>
              </div>
            )
          },
          table({ children, ...props }) {
            return (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200" {...props}>
                  {children}
                </table>
              </div>
            )
          },
          thead({ children, ...props }) {
            return <thead className="bg-gray-50" {...props}>{children}</thead>
          },
          th({ children, ...props }) {
            return (
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                {...props}
              >
                {children}
              </th>
            )
          },
          td({ children, ...props }) {
            return (
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900" {...props}>
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
