/**
 * PixCrawler Design System
 * 
 * Single source of truth: app/globals.css
 * All colors and design tokens are defined as CSS variables.
 * 
 * Usage in components:
 * - Use Tailwind utilities: bg-primary, text-foreground, etc.
 * - Or use CSS variables directly: var(--color-primary-500)
 * 
 * To change brand colors, edit the CSS variables in globals.css only.
 */

// Breakpoints for responsive design
export const breakpoints = {
	sm: '640px',
	md: '768px',
	lg: '1024px',
	xl: '1280px',
	'2xl': '1536px',
} as const

export type Breakpoint = keyof typeof breakpoints
