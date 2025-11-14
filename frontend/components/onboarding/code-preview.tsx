'use client'

import type {DatasetConfig} from '@/app/welcome/welcome-flow'

interface CodePreviewProps {
  config: DatasetConfig
}

function highlightJSON(obj: any, indent = 0): React.ReactNode {
  const indentStr = '  '.repeat(indent)
  const entries = Object.entries(obj)

  return (
    <>
      {'{'}
      {entries.map(([key, value], index) => {
        const isLast = index === entries.length - 1
        return (
          <div key={key}>
            {indentStr}
            <span className="text-blue-400">"{key}"</span>
            <span className="text-muted-foreground">: </span>
            {Array.isArray(value) ? (
              <>
                {'['}
                {value.length > 0 && (
                  <div className="ml-4">
                    {value.map((item, i) => (
                      <div key={i}>
                        {typeof item === 'string' ? (
                          <span className="text-emerald-400">"{item}"</span>
                        ) : Array.isArray(item) ? (
                          <>
                            {'['}
                            {item.map((subItem, j) => (
                              <span key={j}>
                                <span className="text-amber-400">{subItem}</span>
                                {j < item.length - 1 && <span className="text-muted-foreground">, </span>}
                              </span>
                            ))}
                            {']'}
                          </>
                        ) : (
                          <span className="text-amber-400">{JSON.stringify(item)}</span>
                        )}
                        {i < value.length - 1 && <span className="text-muted-foreground">,</span>}
                      </div>
                    ))}
                  </div>
                )}
                <span className="ml-2">{']'}</span>
              </>
            ) : typeof value === 'object' && value !== null ? (
              <div className="ml-4">
                {highlightJSON(value, indent + 1)}
              </div>
            ) : typeof value === 'string' ? (
              <span className="text-emerald-400">"{value}"</span>
            ) : (
              <span className="text-amber-400">{JSON.stringify(value)}</span>
            )}
            {!isLast && <span className="text-muted-foreground">,</span>}
          </div>
        )
      })}
      {indentStr}{'}'}
    </>
  )
}

export function CodePreview({config}: CodePreviewProps) {
  const configJson = {
    dataset_name: config.name,
    categories: {
      animals: config.categories,
    },
    options: {
      max_images: config.imagesPerCategory,
    },
  }

  return (
    <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
      <div
        className="relative px-6 py-4 border-b border-border/50 bg-gradient-to-r from-background via-primary/5 to-background overflow-hidden">
        {/* Animated background shimmer */}
        <div
          className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/10 to-transparent animate-shimmer"/>

        <div className="relative flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-lg rounded-full"/>
              <div
                className="relative size-8 rounded-lg bg-gradient-to-br from-primary/20 to-purple-500/20 border border-primary/30 flex items-center justify-center">
                <svg className="size-4 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/>
                </svg>
              </div>
            </div>
            <div>
              <h3
                className="text-sm font-bold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
                Configuration Preview
              </h3>
              <p className="text-[10px] text-muted-foreground font-medium">Real-time dataset builder</p>
            </div>
          </div>

          <div
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gradient-to-r from-primary/10 via-purple-500/10 to-primary/10 border border-primary/20 backdrop-blur-sm">
            <div className="size-1.5 bg-emerald-500 rounded-full animate-pulse"/>
            <span className="text-xs font-semibold">Building</span>
            <span
              className="text-xs font-bold bg-gradient-to-r from-primary via-purple-500 to-primary bg-clip-text text-transparent">
              animals dataset
            </span>
          </div>
        </div>
      </div>
      <div className="p-6 bg-[#1e1e1e] dark:bg-[#0d1117]">
        <pre className="text-sm font-mono overflow-x-auto">
          <code className="text-gray-200">
            {highlightJSON(configJson)}
          </code>
        </pre>
      </div>
    </div>
  )
}
