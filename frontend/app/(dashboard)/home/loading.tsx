export default function Loading() {
	return (
		<div className="min-h-screen bg-background">
			<div className="border-b border-border">
				<div className="container mx-auto px-4 py-4 flex items-center justify-between animate-pulse">
					<div className="h-8 w-32 bg-muted rounded" />
					<div className="flex gap-4">
						<div className="h-6 w-16 bg-muted rounded" />
						<div className="h-6 w-16 bg-muted rounded" />
					</div>
				</div>
			</div>

			<main className="container mx-auto px-4 py-8 space-y-8 animate-pulse">
				<div className="flex items-center justify-between">
					<div className="h-10 w-48 bg-muted rounded" />
					<div className="h-10 w-32 bg-muted rounded" />
				</div>

				<div className="grid md:grid-cols-4 gap-4">
					{[1, 2, 3, 4].map((i) => (
						<div key={i} className="bg-card border border-border rounded-lg p-6 space-y-2">
							<div className="h-4 w-24 bg-muted rounded" />
							<div className="h-8 w-16 bg-muted rounded" />
						</div>
					))}
				</div>

				<div className="space-y-4">
					<div className="h-7 w-40 bg-muted rounded" />
					<div className="grid md:grid-cols-3 gap-4">
						{[1, 2, 3].map((i) => (
							<div key={i} className="bg-card border border-border rounded-lg p-4 space-y-3">
								<div className="grid grid-cols-2 gap-2">
									<div className="aspect-square bg-muted rounded" />
									<div className="aspect-square bg-muted rounded" />
									<div className="aspect-square bg-muted rounded" />
									<div className="aspect-square bg-muted rounded" />
								</div>
								<div className="h-5 w-24 bg-muted rounded" />
								<div className="flex gap-2">
									<div className="flex-1 h-8 bg-muted rounded" />
									<div className="flex-1 h-8 bg-muted rounded" />
								</div>
							</div>
						))}
					</div>
				</div>
			</main>
		</div>
	)
}
