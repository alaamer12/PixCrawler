import {Metadata} from 'next'

export const metadata: Metadata = {
  title: 'Development Tools - PixCrawler',
  description: 'Development tools and page navigator for PixCrawler',
}

export default function DevLayout({
                                    children,
                                  }: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      <div className="border-b bg-muted/40">
        <div className="container mx-auto px-6 py-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span
              className="px-2 py-1 bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300 rounded text-xs font-medium">
              DEVELOPMENT
            </span>
            <span>•</span>
            <span>This page is only available in development mode</span>
          </div>
        </div>
      </div>
      {children}
    </div>
  )
}
