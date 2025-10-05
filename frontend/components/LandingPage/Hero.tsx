'use client'

import Link from 'next/link'
import { memo } from 'react'

export const Hero = memo(() => {
	return (
		<section className="border-b border-border py-16 md:py-24 lg:py-32">
			<div className="container mx-auto px-4 lg:px-8 text-center">
				<h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 max-w-4xl mx-auto leading-tight">
					Build ML Datasets in Minutes
				</h1>
				<p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
					Automated image dataset creation for machine learning, research, and data science projects
				</p>
				
				<div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
					<Link
						href="/signup"
						className="px-8 py-4 text-base rounded-lg font-medium"
						style={{ backgroundColor: 'var(--primary)', color: 'var(--primary-foreground)' }}
					>
						Get Started Free
					</Link>
					<a
						href="#features"
						className="px-8 py-4 text-base border border-border rounded-lg font-medium hover:bg-muted transition-colors"
					>
						View Demo
					</a>
				</div>

				<div className="max-w-5xl mx-auto h-[300px] md:h-[450px] border-2 border-dashed border-border rounded-lg bg-muted/30 flex items-center justify-center">
					<div className="text-muted-foreground text-sm">
						Hero Visual: Animated Dashboard Preview
					</div>
				</div>
			</div>
		</section>
	)
})
Hero.displayName = 'Hero'
