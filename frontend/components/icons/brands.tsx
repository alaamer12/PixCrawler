import React from 'react'

type Props = { className?: string }

export function GoogleIcon({ className }: Props) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  )
}

export function BingIcon({ className }: Props) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path
        fill="#008373"
        d="M5 3v11.5l7 4.5 5-2.5V13l-4.5 2.5-2.5-1.5L15 12l-6-2.5V3H5z"
      />
      <path
        fill="#00897B"
        d="M12 16.5l5-2.5v3.5l-5 2.5v-3.5z"
      />
    </svg>
  )
}

export function UnsplashIcon({ className }: Props) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path
        fill="currentColor"
        d="M7.5 6.5v4h9v-4h-9zm-3 8h15v6h-15v-6z"
      />
    </svg>
  )
}

export function PixabayIcon({ className }: Props) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path
        fill="#4FC3F7"
        d="M7 3v9h3.5c2.5 0 4.5-2 4.5-4.5S13 3 10.5 3H7zm3.5 2c1.4 0 2.5 1.1 2.5 2.5S11.9 10 10.5 10H9V5h1.5z"
      />
      <path
        fill="#4FC3F7"
        d="M7 10v11h2V10H7z"
      />
    </svg>
  )
}

export function BaiduIcon({ className }: Props) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <ellipse cx="7.5" cy="9" rx="2" ry="2.5" fill="#2932E1" />
      <ellipse cx="16.5" cy="9" rx="2" ry="2.5" fill="#2932E1" />
      <ellipse cx="12" cy="6.5" rx="1.8" ry="2.2" fill="#2932E1" />
      <ellipse cx="4.5" cy="12" rx="1.5" ry="2" fill="#2932E1" />
      <ellipse cx="19.5" cy="12" rx="1.5" ry="2" fill="#2932E1" />
      <path
        fill="#DE3831"
        d="M7 14c0-1 1-2 2.5-2h5c1.5 0 2.5 1 2.5 2v4c0 2-1.5 3-3.5 3h-3c-2 0-3.5-1-3.5-3v-4z"
      />
    </svg>
  )
}

export function DuckDuckGoIcon({ className }: Props) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <circle cx="12" cy="12" r="10" fill="#DE5833" />
      <ellipse cx="12" cy="11" rx="7" ry="6" fill="#66B346" />
      <ellipse cx="12" cy="10" rx="6.5" ry="5.5" fill="#5BAA3C" />
      <circle cx="12" cy="11" r="5.5" fill="#FFFFFF" />
      <path
        fill="#DE5833"
        d="M12 14c-1.5 0-2.8.7-3.5 1.8-.3.4-.1.9.3 1.1.4.2.9.1 1.1-.3.5-.7 1.3-1.1 2.1-1.1s1.6.4 2.1 1.1c.2.4.7.5 1.1.3.4-.2.5-.7.3-1.1C14.8 14.7 13.5 14 12 14z"
      />
      <ellipse cx="10" cy="10" rx="1" ry="1.5" fill="#2D4F8E" />
      <ellipse cx="14" cy="10" rx="1" ry="1.5" fill="#2D4F8E" />
    </svg>
  )
}

export function BrandIcon({ name, className }: { name: string; className?: string }) {
  const size = className || 'size-5'
  switch (name.toLowerCase()) {
    case 'google':
      return <GoogleIcon className={size} />
    case 'bing':
      return <BingIcon className={size} />
    case 'unsplash':
      return <UnsplashIcon className={size} />
    case 'pixabay':
      return <PixabayIcon className={size} />
    case 'baidu':
      return <BaiduIcon className={size} />
    case 'duckduckgo':
      return <DuckDuckGoIcon className={size} />
    default:
      return <UnsplashIcon className={size} />
  }
}