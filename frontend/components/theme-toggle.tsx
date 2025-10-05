'use client'

import { useTheme } from 'next-themes'
import { ThemeSwitcher } from '@/components/ui/shadcn-io/theme-switcher'

export function ThemeToggle() {
	const { theme, setTheme } = useTheme()

	return (
		<ThemeSwitcher
			value={theme as 'light' | 'dark' | 'system'}
			onChange={(newTheme: 'light' | 'dark' | 'system') => setTheme(newTheme)}
		/>
	)
}
