'use client'

import {useCallback, useRef} from 'react'

interface PreloaderConfig {
  preloadBuffer: number
  batchSize: number
  batchDelay: number
  idleTimeout: number
}

interface UseImagePreloaderProps {
  preloadImage: (url: string) => Promise<HTMLImageElement | null>
  config?: Partial<PreloaderConfig>
}

const defaultConfig: PreloaderConfig = {
  preloadBuffer: 20,
  batchSize: 5,
  batchDelay: 100,
  idleTimeout: 1000
}

export const useImagePreloader = ({
                                    preloadImage,
                                    config = {}
                                  }: UseImagePreloaderProps) => {
  const finalConfig = {...defaultConfig, ...config}
  const preloadingRef = useRef<Set<string>>(new Set())

  const preloadImages = useCallback((
    images: Array<{ src: string; [key: string]: any }>,
    startIndex: number,
    direction: 'up' | 'down' = 'down'
  ) => {
    if (!images.length) return

    const {preloadBuffer, batchSize, batchDelay, idleTimeout} = finalConfig

    let startPreload: number
    let endPreload: number

    if (direction === 'down') {
      startPreload = startIndex
      endPreload = Math.min(startIndex + preloadBuffer, images.length)
    } else {
      startPreload = Math.max(0, startIndex - preloadBuffer)
      endPreload = startIndex
    }

    // Create priority map based on distance from current index
    const priorities = new Map<number, number>()
    for (let i = startPreload; i < endPreload; i++) {
      priorities.set(i, Math.abs(i - startIndex))
    }

    // Sort by priority (closest first)
    const sortedIndices = Array.from(priorities.entries())
      .sort((a, b) => a[1] - b[1])
      .map(([index]) => index)

    if (sortedIndices.length === 0) return

    const loadBatch = (batchStart = 0) => {
      const currentBatch = sortedIndices.slice(batchStart, batchStart + batchSize)

      if (currentBatch.length === 0) return

      // Load current batch
      currentBatch.forEach(i => {
        const image = images[i]
        if (image && !preloadingRef.current.has(image.src)) {
          preloadingRef.current.add(image.src)
          preloadImage(image.src).finally(() => {
            preloadingRef.current.delete(image.src)
          })
        }
      })

      // Schedule next batch
      if (batchStart + batchSize < sortedIndices.length) {
        setTimeout(() => loadBatch(batchStart + batchSize), batchDelay)
      }
    }

    // Use requestIdleCallback for better performance
    if ('requestIdleCallback' in window) {
      requestIdleCallback(() => loadBatch(), {timeout: idleTimeout})
    } else {
      // Fallback for browsers without requestIdleCallback
      setTimeout(() => loadBatch(), 0)
    }
  }, [preloadImage, finalConfig])

  const preloadRange = useCallback((
    images: Array<{ src: string; [key: string]: any }>,
    startIndex: number,
    endIndex: number
  ) => {
    const validStart = Math.max(0, startIndex)
    const validEnd = Math.min(images.length, endIndex)

    for (let i = validStart; i < validEnd; i++) {
      const image = images[i]
      if (image && !preloadingRef.current.has(image.src)) {
        preloadingRef.current.add(image.src)
        preloadImage(image.src).finally(() => {
          preloadingRef.current.delete(image.src)
        })
      }
    }
  }, [preloadImage])

  const isPreloading = useCallback((src: string) => {
    return preloadingRef.current.has(src)
  }, [])

  const getPreloadingCount = useCallback(() => {
    return preloadingRef.current.size
  }, [])

  return {
    preloadImages,
    preloadRange,
    isPreloading,
    getPreloadingCount
  }
}
