/**
 * Simple centered loading spinner
 * Used for: Root loading, auth pages
 */
export function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"/>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  )
}

/**
 * Page skeleton with header and content area
 * Used for: Dashboard pages (home, profile, datasets, etc.)
 */
export function PageLoadingSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <div className="border-b border-border">
        <div className="container mx-auto px-4 py-4 animate-pulse">
          <div className="h-8 w-32 bg-muted rounded"/>
        </div>
      </div>
      <main className="container mx-auto px-4 py-8 animate-pulse">
        <div className="space-y-4">
          <div className="h-10 w-48 bg-muted rounded"/>
          <div className="h-64 bg-muted rounded"/>
        </div>
      </main>
    </div>
  )
}
