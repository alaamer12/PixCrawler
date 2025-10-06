import Link from 'next/link'
import {Button} from '@/components/ui/button'

/**
 * Reusable 404 UI component
 * Used by not-found.tsx files throughout the app
 */
export function NotFoundUI() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="max-w-md w-full space-y-6 text-center">
        <div className="space-y-2">
          <div className="text-6xl">404</div>
          <h1 className="text-2xl font-bold">Page Not Found</h1>
          <p className="text-muted-foreground">
            The page you're looking for doesn't exist or has been moved.
          </p>
        </div>

        <div className="flex gap-4 justify-center">
          <Button asChild>
            <Link href="/">
              Go Home
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/datasets">
              View Datasets
            </Link>
          </Button>
        </div>
      </div>
    </div>
  )
}
