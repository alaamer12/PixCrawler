'use client'

import {useEffect} from 'react'
import {Button} from '@/components/ui/button'

/**
 * Global error boundary - catches errors in root layout
 * Must define its own <html> and <body> tags
 */
export default function GlobalError({
                                      error,
                                      reset,
                                    }: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error('Global error:', error)
  }, [error])

  return (
    <html lang="en">
    <body>
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-6 text-center">
        <div className="space-y-2">
          <div className="text-6xl">💥</div>
          <h1 className="text-2xl font-bold">Critical Error</h1>
          <p className="text-muted-foreground">
            A critical error occurred. Please refresh the page.
          </p>
          {error.digest && (
            <p className="text-xs text-muted-foreground font-mono">
              Error ID: {error.digest}
            </p>
          )}
        </div>

        <Button onClick={reset} variant="destructive">
          Reload Application
        </Button>
      </div>
    </div>
    </body>
    </html>
  )
}
