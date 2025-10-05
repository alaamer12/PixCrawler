import Link from 'next/link'

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
					<Link
						href="/"
						className="px-6 py-3 rounded-lg font-medium transition-colors"
						style={{ backgroundColor: 'var(--primary)', color: 'var(--primary-foreground)' }}
					>
						Go Home
					</Link>
					<Link
						href="/datasets"
						className="px-6 py-3 bg-muted text-foreground rounded-lg font-medium hover:bg-muted/80 transition-colors"
					>
						View Datasets
					</Link>
				</div>
			</div>
		</div>
	)
}
