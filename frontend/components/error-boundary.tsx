'use client'

import {useEffect} from 'react'
import {Button} from '@/components/ui/button'

interface ErrorBoundaryProps {
  error: Error & { digest?: string }
  reset: () => void
}

/**
 * Reusable error UI component
 * Used by error.tsx files throughout the app
 */
export function ErrorBoundary({error, reset}: ErrorBoundaryProps) {
  useEffect(() => {
    // Log error to monitoring service (e.g., Sentry)
    console.error('Error caught by boundary:', error)
  }, [error])

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-6 text-center">
        <div className="space-y-2">
          <div className="text-6xl">⚠️</div>
          <h1 className="text-2xl font-bold">Something went wrong</h1>
          <p className="text-muted-foreground">
            {error.message || 'An unexpected error occurred'}
          </p>
          {error.digest && (
            <p className="text-xs text-muted-foreground font-mono">
              Error ID: {error.digest}
            </p>
          )}
        </div>

        <div className="flex gap-4 justify-center">
          <Button onClick={reset}>
            Try Again
          </Button>
          <Button asChild variant="outline">
            <a href="/">
              Go Home
            </a>
          </Button>
        </div>
      </div>
    </div>
  )
}
