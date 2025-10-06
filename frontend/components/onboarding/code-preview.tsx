'use client'

import type { DatasetConfig } from '@/app/welcome/welcome-flow'

interface CodePreviewProps {
  config: DatasetConfig
}

export function CodePreview({ config }: CodePreviewProps) {
  const configJson = {
    name: config.name,
    categories: config.categories,
    max_images_per_category: config.imagesPerCategory,
    engines: ['primary', 'secondary'],
    quality_filters: {
      min_resolution: [224, 224],
    },
  }

  const jsonString = JSON.stringify(configJson, null, 2)

  return (
    <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-border bg-muted/30">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Live Configuration Preview
        </h3>
      </div>
      <div className="p-6">
        <pre className="text-sm font-mono text-foreground overflow-x-auto">
          <code>{jsonString}</code>
        </pre>
      </div>
    </div>
  )
}