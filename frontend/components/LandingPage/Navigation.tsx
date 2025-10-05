'use client'

import Link from 'next/link'
import { memo, useState } from 'react'
import { Menu, X } from 'lucide-react'
import { ThemeToggle } from '@/components/theme-toggle'

const NavLinks = memo(() => (
	<div className="hidden md:flex gap-8">
		<a href="#features" className="text-sm hover:text-primary transition-colors">
			Features
		</a>
		<a href="#pricing" className="text-sm hover:text-primary transition-colors">
			Pricing
		</a>
		<a href="#docs" className="text-sm hover:text-primary transition-colors">
			Docs
		</a>
		<a href="#blog" className="text-sm hover:text-primary transition-colors">
			Blog
		</a>
	</div>
))
NavLinks.displayName = 'NavLinks'

const AuthButtons = memo(() => (
	<div className="flex items-center gap-3">
		<ThemeToggle />
		<Link
			href="/login"
			className="px-5 py-2 text-sm border border-border rounded-lg hover:bg-muted transition-colors"
		>
			Sign In
		</Link>
	</div>
))
AuthButtons.displayName = 'AuthButtons'

export const Navigation = memo(() => {
	const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

	return (
		<>
			<nav className="border-b border-border sticky top-0 bg-background/95 backdrop-blur z-50">
				<div className="container mx-auto px-4 lg:px-8 h-[70px] flex items-center justify-between">
					<Link href="/" className="text-xl font-bold">
						PixCrawler
					</Link>
					<NavLinks />
					<div className="flex items-center gap-3">
						<AuthButtons />
						<button
							onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
							className="md:hidden w-9 h-9 border border-border rounded flex items-center justify-center hover:bg-muted transition-colors"
							aria-label="Toggle menu"
						>
							{mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
						</button>
					</div>
				</div>
			</nav>

			{/* Mobile Menu */}
			{mobileMenuOpen && (
				<div className="md:hidden fixed inset-0 top-[70px] bg-background/95 backdrop-blur z-40 border-b border-border">
					<div className="container mx-auto px-4 py-6 flex flex-col gap-4">
						<a
							href="#features"
							className="text-base hover:text-primary transition-colors py-2"
							onClick={() => setMobileMenuOpen(false)}
						>
							Features
						</a>
						<a
							href="#pricing"
							className="text-base hover:text-primary transition-colors py-2"
							onClick={() => setMobileMenuOpen(false)}
						>
							Pricing
						</a>
						<a
							href="#docs"
							className="text-base hover:text-primary transition-colors py-2"
							onClick={() => setMobileMenuOpen(false)}
						>
							Docs
						</a>
						<a
							href="#blog"
							className="text-base hover:text-primary transition-colors py-2"
							onClick={() => setMobileMenuOpen(false)}
						>
							Blog
						</a>
						<div className="border-t border-border pt-4 mt-2">
							<Link
								href="/login"
								className="px-5 py-3 text-center border border-border rounded-lg hover:bg-muted transition-colors block"
							>
								Sign In
							</Link>
						</div>
					</div>
				</div>
			)}
		</>
	)
})
Navigation.displayName = 'Navigation'
