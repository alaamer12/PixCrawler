'use client'

import { useCallback, useRef } from 'react'

interface UseNextImagePreloaderReturn {
  preloadImages: (urls: string[]) => void
  preloadImage: (url: string) => void
  clearPreloads: () => void
}

export const useNextImagePreloader = (): UseNextImagePreloaderReturn => {
  const preloadedUrls = useRef<Set<string>>(new Set())
  const preloadElements = useRef<HTMLLinkElement[]>([])

  const preloadImage = useCallback((url: string) => {
    if (preloadedUrls.current.has(url)) return

    const link = document.createElement('link')
    link.rel = 'preload'
    link.as = 'image'
    link.href = url
    
    document.head.appendChild(link)
    preloadElements.current.push(link)
    preloadedUrls.current.add(url)

    // Clean up after 30 seconds
    setTimeout(() => {
      if (document.head.contains(link)) {
        document.head.removeChild(link)
        const index = preloadElements.current.indexOf(link)
        if (index > -1) {
          preloadElements.current.splice(index, 1)
        }
      }
    }, 30000)
  }, [])

  const preloadImages = useCallback((urls: string[]) => {
    urls.forEach(url => preloadImage(url))
  }, [preloadImage])

  const clearPreloads = useCallback(() => {
    preloadElements.current.forEach(link => {
      if (document.head.contains(link)) {
        document.head.removeChild(link)
      }
    })
    preloadElements.current = []
    preloadedUrls.current.clear()
  }, [])

  return {
    preloadImages,
    preloadImage,
    clearPreloads
  }
}