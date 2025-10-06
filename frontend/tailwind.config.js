/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-manrope)', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
      },
      transitionDuration: {
        fast: '150ms',
        base: '300ms',
        slow: '400ms',
        slower: '600ms',
      },
      keyframes: {
        fadeIn: {
          '0%': {opacity: '0'},
          '100%': {opacity: '1'},
        },
        fadeOut: {
          '0%': {opacity: '1'},
          '100%': {opacity: '0'},
        },
        slideInFromTop: {
          '0%': {transform: 'translateY(-100%)'},
          '100%': {transform: 'translateY(0)'},
        },
        slideInFromBottom: {
          '0%': {transform: 'translateY(100%)'},
          '100%': {transform: 'translateY(0)'},
        },
        slideInFromLeft: {
          '0%': {transform: 'translateX(-100%)'},
          '100%': {transform: 'translateX(0)'},
        },
        slideInFromRight: {
          '0%': {transform: 'translateX(100%)'},
          '100%': {transform: 'translateX(0)'},
        },
        scaleIn: {
          '0%': {transform: 'scale(0.95)', opacity: '0'},
          '100%': {transform: 'scale(1)', opacity: '1'},
        },
        scaleOut: {
          '0%': {transform: 'scale(1)', opacity: '1'},
          '100%': {transform: 'scale(0.95)', opacity: '0'},
        },
      },
      animation: {
        fadeIn: 'fadeIn 300ms ease-out',
        fadeOut: 'fadeOut 300ms ease-out',
        slideInFromTop: 'slideInFromTop 300ms ease-out',
        slideInFromBottom: 'slideInFromBottom 300ms ease-out',
        slideInFromLeft: 'slideInFromLeft 300ms ease-out',
        slideInFromRight: 'slideInFromRight 300ms ease-out',
        scaleIn: 'scaleIn 300ms ease-out',
        scaleOut: 'scaleOut 300ms ease-out',
      },
    },
  },
  plugins: [],
}
