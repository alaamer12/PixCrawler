'use client'

import Link from 'next/link'
import { memo } from 'react'

const NavLinks = memo(() => (
	<div className="hidden md:flex gap-8">
		<a href="#features" className="text-sm hover:text-primary transition-colors">
			Features
		</a>
		<a href="#how-it-works" className="text-sm hover:text-primary transition-colors">
			How It Works
		</a>
		<a href="#use-cases" className="text-sm hover:text-primary transition-colors">
			Use Cases
		</a>
	</div>
))
NavLinks.displayName = 'NavLinks'

const AuthButtons = memo(() => (
	<div className="flex gap-3">
		<Link
			href="/login"
			className="hidden sm:block px-5 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors"
		>
			Sign In
		</Link>
		<Link
			href="/signup"
			className="px-5 py-2 text-sm rounded-lg font-medium"
			style={{ backgroundColor: 'var(--primary)', color: 'var(--primary-foreground)' }}
		>
			Get Started
		</Link>
	</div>
))
AuthButtons.displayName = 'AuthButtons'

export const Navigation = memo(() => {
	return (
		<nav className="border-b border-border sticky top-0 bg-background/95 backdrop-blur z-50">
			<div className="container mx-auto px-4 lg:px-8 h-[70px] flex items-center justify-between">
				<Link href="/" className="text-xl font-bold">
					PixCrawler
				</Link>
				<NavLinks />
				<AuthButtons />
			</div>
		</nav>
	)
})
Navigation.displayName = 'Navigation'
