'use client'

import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useEffect, useState } from 'react'

export function ThemeToggle() {
	const { theme, setTheme } = useTheme()
	const [mounted, setMounted] = useState(false)

	// Avoid hydration mismatch
	useEffect(() => {
		setMounted(true)
	}, [])

	if (!mounted) {
		return (
			<div className="w-9 h-9 border border-border rounded flex items-center justify-center">
				<div className="w-4 h-4" />
			</div>
		)
	}

	return (
		<button
			onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
			className="w-9 h-9 border border-border rounded flex items-center justify-center hover:bg-muted transition-colors"
			aria-label="Toggle theme"
		>
			{theme === 'dark' ? (
				<Sun className="h-4 w-4" />
			) : (
				<Moon className="h-4 w-4" />
			)}
		</button>
	)
}
